import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeInvalidError, 
    PhoneCodeExpiredError, 
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    ApiIdInvalidError
)
from typing import Dict, Optional, Any
import os

from app.services.supabase_service import supabase_service
from app.config import settings

class TelegramAuthService:
    def __init__(self):
        self.temp_clients: Dict[str, TelegramClient] = {}
    
    async def start_auth_process(self, phone_number: str, api_id: int, api_hash: str) -> Dict[str, Any]:
        """텔레그램 인증 프로세스 시작"""
        try:
            # 기존 계정 확인
            existing_account = await supabase_service.get_account_by_phone(phone_number)
            if existing_account:
                return {
                    "success": False,
                    "error": "이미 등록된 전화번호입니다.",
                    "account_id": existing_account["id"]
                }
            
            # 임시 클라이언트 생성
            session_name = f"temp_{phone_number.replace('+', '')}"
            client = TelegramClient(StringSession(""), api_id, api_hash)
            
            # 클라이언트 연결
            await client.connect()
            
            # 전화번호 유효성 검사
            if not await client.is_user_authorized():
                # 인증 코드 요청
                await client.send_code_request(phone_number)
                
                # 임시 클라이언트 저장
                self.temp_clients[phone_number] = client
                
                return {
                    "success": True,
                    "message": "인증 코드가 전송되었습니다.",
                    "phone_number": phone_number,
                    "requires_code": True
                }
            else:
                # 이미 인증된 경우
                me = await client.get_me()
                session_string = client.session.save()
                
                # 계정 정보 저장
                account_data = {
                    "phone_number": phone_number,
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "session_string": session_string,
                    "user_id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "is_verified": True,
                    "is_active": True
                }
                
                account = await supabase_service.create_account(account_data)
                
                await client.disconnect()
                
                return {
                    "success": True,
                    "message": "인증이 완료되었습니다.",
                    "account": account,
                    "requires_code": False
                }
                
        except PhoneNumberInvalidError:
            return {
                "success": False,
                "error": "유효하지 않은 전화번호입니다."
            }
        except ApiIdInvalidError:
            return {
                "success": False,
                "error": "유효하지 않은 API ID 또는 API Hash입니다."
            }
        except Exception as e:
            print(f"Error starting auth process: {e}")
            return {
                "success": False,
                "error": f"인증 프로세스 시작 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def verify_code(self, phone_number: str, code: str) -> Dict[str, Any]:
        """인증 코드 확인"""
        try:
            if phone_number not in self.temp_clients:
                return {
                    "success": False,
                    "error": "인증 프로세스가 만료되었습니다. 다시 시작해주세요."
                }
            
            client = self.temp_clients[phone_number]
            
            try:
                # 코드로 로그인 시도
                await client.sign_in(phone_number, code)
                
                # 2FA 확인
                if await client.is_user_authorized():
                    me = await client.get_me()
                    session_string = client.session.save()
                    
                    # 계정 정보 저장
                    account_data = {
                        "phone_number": phone_number,
                        "api_id": client.api_id,
                        "api_hash": client.api_hash,
                        "session_string": session_string,
                        "user_id": me.id,
                        "username": me.username,
                        "first_name": me.first_name,
                        "last_name": me.last_name,
                        "is_verified": True,
                        "is_active": True
                    }
                    
                    account = await supabase_service.create_account(account_data)
                    
                    # 임시 클라이언트 정리
                    await client.disconnect()
                    del self.temp_clients[phone_number]
                    
                    return {
                        "success": True,
                        "message": "인증이 완료되었습니다.",
                        "account": account
                    }
                else:
                    return {
                        "success": False,
                        "error": "인증에 실패했습니다."
                    }
                    
            except PhoneCodeInvalidError:
                return {
                    "success": False,
                    "error": "잘못된 인증 코드입니다."
                }
            except PhoneCodeExpiredError:
                return {
                    "success": False,
                    "error": "인증 코드가 만료되었습니다. 다시 요청해주세요."
                }
            except SessionPasswordNeededError:
                # 2FA 비밀번호 필요
                return {
                    "success": True,
                    "message": "2FA 비밀번호가 필요합니다.",
                    "requires_2fa": True,
                    "phone_number": phone_number
                }
                
        except Exception as e:
            print(f"Error verifying code: {e}")
            return {
                "success": False,
                "error": f"코드 확인 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def verify_2fa(self, phone_number: str, password: str) -> Dict[str, Any]:
        """2FA 비밀번호 확인"""
        try:
            if phone_number not in self.temp_clients:
                return {
                    "success": False,
                    "error": "인증 프로세스가 만료되었습니다. 다시 시작해주세요."
                }
            
            client = self.temp_clients[phone_number]
            
            try:
                # 2FA 비밀번호로 로그인
                await client.sign_in(password=password)
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    session_string = client.session.save()
                    
                    # 계정 정보 저장
                    account_data = {
                        "phone_number": phone_number,
                        "api_id": client.api_id,
                        "api_hash": client.api_hash,
                        "session_string": session_string,
                        "user_id": me.id,
                        "username": me.username,
                        "first_name": me.first_name,
                        "last_name": me.last_name,
                        "is_verified": True,
                        "is_active": True
                    }
                    
                    account = await supabase_service.create_account(account_data)
                    
                    # 임시 클라이언트 정리
                    await client.disconnect()
                    del self.temp_clients[phone_number]
                    
                    return {
                        "success": True,
                        "message": "2FA 인증이 완료되었습니다.",
                        "account": account
                    }
                else:
                    return {
                        "success": False,
                        "error": "2FA 인증에 실패했습니다."
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": "잘못된 2FA 비밀번호입니다."
                }
                
        except Exception as e:
            print(f"Error verifying 2FA: {e}")
            return {
                "success": False,
                "error": f"2FA 확인 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def test_connection(self, account_id: int) -> Dict[str, Any]:
        """계정 연결 테스트"""
        try:
            account = await supabase_service.get_account(account_id)
            if not account:
                return {
                    "success": False,
                    "error": "계정을 찾을 수 없습니다."
                }
            
            # 클라이언트 생성 및 연결 테스트
            client = TelegramClient(
                StringSession(account["session_string"]),
                account["api_id"],
                account["api_hash"]
            )
            
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                
                return {
                    "success": True,
                    "message": "연결이 정상입니다.",
                    "user_info": {
                        "id": me.id,
                        "username": me.username,
                        "first_name": me.first_name,
                        "last_name": me.last_name
                    }
                }
            else:
                await client.disconnect()
                return {
                    "success": False,
                    "error": "세션이 만료되었습니다. 재인증이 필요합니다."
                }
                
        except Exception as e:
            print(f"Error testing connection: {e}")
            return {
                "success": False,
                "error": f"연결 테스트 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def revoke_session(self, account_id: int) -> Dict[str, Any]:
        """세션 취소 (계정 비활성화)"""
        try:
            account = await supabase_service.get_account(account_id)
            if not account:
                return {
                    "success": False,
                    "error": "계정을 찾을 수 없습니다."
                }
            
            # 계정 비활성화
            await supabase_service.update_account(account_id, {"is_active": False})
            
            return {
                "success": True,
                "message": "세션이 취소되었습니다."
            }
            
        except Exception as e:
            print(f"Error revoking session: {e}")
            return {
                "success": False,
                "error": f"세션 취소 중 오류가 발생했습니다: {str(e)}"
            }
    
    def cleanup_temp_clients(self):
        """임시 클라이언트 정리"""
        for phone_number, client in self.temp_clients.items():
            try:
                asyncio.create_task(client.disconnect())
            except:
                pass
        self.temp_clients.clear()

# 전역 인스턴스
telegram_auth_service = TelegramAuthService() 
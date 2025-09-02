"""
File service for handling file operations
파일 관리 서비스
"""

import mimetypes
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class FileService:
    """파일 관리 서비스"""

    def __init__(self, base_dir: str = "."):
        """초기화"""
        self.base_dir = Path(base_dir)
        self.allowed_extensions = {
            'mbox': ['.mbox'],
            'evidence': ['.html', '.pdf'],
            'attachment': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.png', '.zip'],
            'export': ['.json', '.csv', '.html']
        }

    def validate_file(self, file_path: Union[str, Path], file_type: str = 'any') -> Dict[str, Any]:
        """파일 유효성 검사"""
        file_path = Path(file_path)

        result = {
            'valid': False,
            'exists': file_path.exists(),
            'size': 0,
            'extension': '',
            'mime_type': '',
            'message': ''
        }

        if not result['exists']:
            result['message'] = '파일이 존재하지 않습니다.'
            return result

        try:
            stat = file_path.stat()
            result['size'] = stat.st_size
            result['extension'] = file_path.suffix.lower()

            # MIME 타입 추정
            mime_type, _ = mimetypes.guess_type(str(file_path))
            result['mime_type'] = mime_type or 'application/octet-stream'

            # 확장자 검사
            if file_type != 'any':
                allowed = self.allowed_extensions.get(file_type, [])
                if allowed and result['extension'] not in allowed:
                    result['message'] = f'허용되지 않는 파일 형식입니다. 허용: {", ".join(allowed)}'
                    return result

            # 파일 크기 검사
            if result['size'] == 0:
                result['message'] = '빈 파일입니다.'
                return result

            result['valid'] = True
            result['message'] = '유효한 파일입니다.'

        except Exception as e:
            result['message'] = f'파일 검사 오류: {str(e)}'

        return result

    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """파일 정보 조회"""
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                'exists': False,
                'message': '파일이 존재하지 않습니다.'
            }

        try:
            stat = file_path.stat()

            return {
                'exists': True,
                'name': file_path.name,
                'path': str(file_path.absolute()),
                'size': stat.st_size,
                'size_human': self._format_size(stat.st_size),
                'extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0] or 'unknown',
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_directory': file_path.is_dir()
            }

        except Exception as e:
            return {
                'exists': True,
                'error': f'파일 정보 조회 오류: {str(e)}'
            }

    def _format_size(self, size_bytes: int) -> str:
        """파일 크기를 사람이 읽기 쉬운 형태로 변환"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def list_directory(self, directory_path: Union[str, Path], file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """디렉토리 내용 목록"""
        directory_path = Path(directory_path)

        if not directory_path.exists() or not directory_path.is_dir():
            return []

        files = []

        try:
            for item in directory_path.iterdir():
                try:
                    # 파일 타입 필터링
                    if file_type and file_type != 'all':
                        allowed_extensions = self.allowed_extensions.get(
                            file_type, [])
                        if allowed_extensions and item.suffix.lower() not in allowed_extensions:
                            continue

                    file_info = self.get_file_info(item)
                    if file_info.get('exists'):
                        files.append(file_info)

                except Exception as e:
                    print(f"파일 정보 조회 오류 ({item.name}): {e}")
                    continue

        except Exception as e:
            print(f"디렉토리 읽기 오류: {e}")

        # 이름순 정렬
        files.sort(key=lambda x: (
            x.get('is_directory', False), x.get('name', '')))
        return files

    def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> Dict[str, Any]:
        """파일 복사"""
        source = Path(source)
        destination = Path(destination)

        if not source.exists():
            return {
                'success': False,
                'message': '원본 파일이 존재하지 않습니다.'
            }

        try:
            # 대상 디렉토리 생성
            destination.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source, destination)

            return {
                'success': True,
                'message': f'파일이 성공적으로 복사되었습니다: {destination}',
                'destination': str(destination)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'파일 복사 오류: {str(e)}'
            }

    def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> Dict[str, Any]:
        """파일 이동"""
        source = Path(source)
        destination = Path(destination)

        if not source.exists():
            return {
                'success': False,
                'message': '원본 파일이 존재하지 않습니다.'
            }

        try:
            # 대상 디렉토리 생성
            destination.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(source), str(destination))

            return {
                'success': True,
                'message': f'파일이 성공적으로 이동되었습니다: {destination}',
                'destination': str(destination)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'파일 이동 오류: {str(e)}'
            }

    def delete_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """파일 삭제"""
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                'success': False,
                'message': '삭제할 파일이 존재하지 않습니다.'
            }

        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()

            return {
                'success': True,
                'message': f'{"디렉토리" if file_path.is_dir() else "파일"}가 성공적으로 삭제되었습니다.'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'삭제 오류: {str(e)}'
            }

    def create_zip_archive(self, source_paths: List[Union[str, Path]], zip_path: Union[str, Path]) -> Dict[str, Any]:
        """ZIP 아카이브 생성"""
        zip_path = Path(zip_path)

        try:
            # 대상 디렉토리 생성
            zip_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                total_files = 0

                for source_path in source_paths:
                    source_path = Path(source_path)

                    if not source_path.exists():
                        continue

                    if source_path.is_file():
                        zipf.write(source_path, source_path.name)
                        total_files += 1
                    elif source_path.is_dir():
                        for file_path in source_path.rglob('*'):
                            if file_path.is_file():
                                # 상대 경로로 저장
                                arcname = file_path.relative_to(
                                    source_path.parent)
                                zipf.write(file_path, arcname)
                                total_files += 1

            return {
                'success': True,
                'message': f'ZIP 아카이브가 생성되었습니다: {zip_path}',
                'zip_path': str(zip_path),
                'total_files': total_files,
                'zip_size': zip_path.stat().st_size
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'ZIP 생성 오류: {str(e)}'
            }

    def extract_zip_archive(self, zip_path: Union[str, Path], extract_to: Union[str, Path]) -> Dict[str, Any]:
        """ZIP 아카이브 추출"""
        zip_path = Path(zip_path)
        extract_to = Path(extract_to)

        if not zip_path.exists():
            return {
                'success': False,
                'message': 'ZIP 파일이 존재하지 않습니다.'
            }

        try:
            extract_to.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_to)
                extracted_files = zipf.namelist()

            return {
                'success': True,
                'message': f'ZIP 파일이 추출되었습니다: {extract_to}',
                'extract_path': str(extract_to),
                'extracted_files': len(extracted_files),
                'files': extracted_files
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'ZIP 추출 오류: {str(e)}'
            }

    def get_disk_usage(self, path: Union[str, Path]) -> Dict[str, Any]:
        """디스크 사용량 조회"""
        path = Path(path)

        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)

                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(path)),
                    ctypes.pointer(free_bytes),
                    ctypes.pointer(total_bytes),
                    None
                )

                total = total_bytes.value
                free = free_bytes.value
                used = total - free
            else:  # Unix/Linux
                stat = os.statvfs(str(path))
                total = stat.f_frsize * stat.f_blocks
                free = stat.f_frsize * stat.f_available
                used = total - free

            return {
                'success': True,
                'total': total,
                'used': used,
                'free': free,
                'total_human': self._format_size(total),
                'used_human': self._format_size(used),
                'free_human': self._format_size(free),
                'usage_percent': (used / total * 100) if total > 0 else 0
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'디스크 사용량 조회 오류: {str(e)}'
            }

    def clean_temp_files(self, temp_dir: Union[str, Path] = "temp") -> Dict[str, Any]:
        """임시 파일 정리"""
        temp_dir = Path(temp_dir)

        if not temp_dir.exists():
            return {
                'success': True,
                'message': '임시 디렉토리가 존재하지 않습니다.',
                'cleaned_files': 0
            }

        try:
            cleaned_count = 0
            cleaned_size = 0

            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += file_size
                    except Exception as e:
                        print(f"임시 파일 삭제 오류 ({file_path.name}): {e}")

            return {
                'success': True,
                'message': f'{cleaned_count}개의 임시 파일이 정리되었습니다.',
                'cleaned_files': cleaned_count,
                'cleaned_size': self._format_size(cleaned_size)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'임시 파일 정리 오류: {str(e)}'
            }

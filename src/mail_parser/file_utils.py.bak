"""
File handling utilities.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Union, List
import re


def ensure_directory(path: Union[str, Path]) -> Path:
    """디렉터리가 존재하지 않으면 생성합니다."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str, max_length: int = 200) -> str:
    """파일명을 안전하게 정리합니다."""
    if not filename:
        return "unnamed"

    # 위험한 문자 제거
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    safe = re.sub(unsafe_chars, '_', filename)

    # 공백을 언더스코어로
    safe = safe.replace(' ', '_')

    # 연속된 언더스코어 정리
    safe = re.sub(r'_+', '_', safe)

    # 앞뒤 공백과 점 제거
    safe = safe.strip('._')

    # 길이 제한
    if len(safe) > max_length:
        name, ext = safe.rsplit('.', 1) if '.' in safe else (safe, '')
        if ext:
            name = name[:max_length - len(ext) - 1]
            safe = f"{name}.{ext}"
        else:
            safe = safe[:max_length]

    return safe or "unnamed"


def get_unique_filename(directory: Union[str, Path], filename: str) -> Path:
    """중복되지 않는 파일명을 생성합니다."""
    directory = Path(directory)
    ensure_directory(directory)

    base_path = directory / filename

    if not base_path.exists():
        return base_path

    # 파일명과 확장자 분리
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')

    counter = 1
    while True:
        if ext:
            new_filename = f"{name}_{counter}.{ext}"
        else:
            new_filename = f"{name}_{counter}"

        new_path = directory / new_filename
        if not new_path.exists():
            return new_path

        counter += 1


def copy_file_safe(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """파일을 안전하게 복사합니다."""
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return False

        # 대상 디렉터리 생성
        ensure_directory(dst_path.parent)

        # 파일 복사
        shutil.copy2(src_path, dst_path)
        return True

    except Exception as e:
        print(f"파일 복사 오류 ({src} -> {dst}): {e}")
        return False


def move_file_safe(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """파일을 안전하게 이동합니다."""
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return False

        # 대상 디렉터리 생성
        ensure_directory(dst_path.parent)

        # 파일 이동
        shutil.move(str(src_path), str(dst_path))
        return True

    except Exception as e:
        print(f"파일 이동 오류 ({src} -> {dst}): {e}")
        return False


def delete_file_safe(path: Union[str, Path]) -> bool:
    """파일을 안전하게 삭제합니다."""
    try:
        path = Path(path)
        if path.exists():
            path.unlink()
        return True
    except Exception as e:
        print(f"파일 삭제 오류 ({path}): {e}")
        return False


def get_file_size_human(path: Union[str, Path]) -> str:
    """사람이 읽기 쉬운 파일 크기를 반환합니다."""
    try:
        size = Path(path).stat().st_size

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0

        return f"{size:.1f} PB"

    except Exception:
        return "알 수 없음"


def find_files_by_extension(directory: Union[str, Path], extensions: List[str]) -> List[Path]:
    """지정된 확장자를 가진 파일들을 찾습니다."""
    directory = Path(directory)

    if not directory.exists():
        return []

    files = []
    extensions = [ext.lower().lstrip('.') for ext in extensions]

    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower().lstrip('.') in extensions:
            files.append(file_path)

    return files


def cleanup_empty_directories(directory: Union[str, Path]) -> int:
    """빈 디렉터리들을 정리합니다."""
    directory = Path(directory)
    removed_count = 0

    try:
        # 하위 디렉터리부터 검사
        for dir_path in sorted(directory.rglob("*"), key=lambda p: -len(p.parts)):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    removed_count += 1
                except OSError:
                    pass  # 삭제할 수 없는 디렉터리는 무시

    except Exception as e:
        print(f"디렉터리 정리 오류: {e}")

    return removed_count


def get_directory_size(directory: Union[str, Path]) -> int:
    """디렉터리의 전체 크기를 계산합니다."""
    directory = Path(directory)
    total_size = 0

    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception as e:
        print(f"디렉터리 크기 계산 오류: {e}")

    return total_size


def backup_file(file_path: Union[str, Path], backup_suffix: str = ".bak") -> Optional[Path]:
    """파일을 백업합니다."""
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)

        # 중복 백업 방지
        counter = 1
        while backup_path.exists():
            backup_path = file_path.with_suffix(
                f"{file_path.suffix}{backup_suffix}.{counter}")
            counter += 1

        shutil.copy2(file_path, backup_path)
        return backup_path

    except Exception as e:
        print(f"파일 백업 오류 ({file_path}): {e}")
        return None


def is_text_file(file_path: Union[str, Path], chunk_size: int = 1024) -> bool:
    """파일이 텍스트 파일인지 확인합니다."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)

        # NULL 바이트가 있으면 바이너리 파일로 간주
        if b'\x00' in chunk:
            return False

        # 텍스트로 디코딩 시도
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            try:
                chunk.decode('cp949')
                return True
            except UnicodeDecodeError:
                return False

    except Exception:
        return False

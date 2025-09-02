"""
Hash calculation utilities.
"""

import hashlib
from pathlib import Path
from typing import Union, Optional


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """파일의 해시를 계산합니다."""
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")

        hasher = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    except Exception as e:
        print(f"파일 해시 계산 오류 ({file_path}): {e}")
        return ""


def calculate_data_hash(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """데이터의 해시를 계산합니다."""
    try:
        hasher = hashlib.new(algorithm)

        if isinstance(data, str):
            hasher.update(data.encode('utf-8'))
        else:
            hasher.update(data)

        return hasher.hexdigest()

    except Exception as e:
        print(f"데이터 해시 계산 오류: {e}")
        return ""


def calculate_directory_hash(directory: Union[str, Path], algorithm: str = 'sha256') -> str:
    """디렉터리 내 모든 파일의 해시를 계산합니다."""
    try:
        directory = Path(directory)

        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"유효하지 않은 디렉터리: {directory}")

        hasher = hashlib.new(algorithm)

        # 파일을 이름순으로 정렬하여 일관된 해시 생성
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file():
                # 상대 경로를 해시에 포함 (디렉터리 구조 반영)
                relative_path = file_path.relative_to(directory)
                hasher.update(str(relative_path).encode('utf-8'))

                # 파일 내용 해시
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)

        return hasher.hexdigest()

    except Exception as e:
        print(f"디렉터리 해시 계산 오류 ({directory}): {e}")
        return ""


def verify_file_hash(file_path: Union[str, Path], expected_hash: str, algorithm: str = 'sha256') -> bool:
    """파일 해시를 검증합니다."""
    current_hash = calculate_file_hash(file_path, algorithm)
    return current_hash.lower() == expected_hash.lower()


def get_supported_algorithms() -> list:
    """지원되는 해시 알고리즘 목록을 반환합니다."""
    return list(hashlib.algorithms_guaranteed)


def calculate_multiple_hashes(data: Union[str, bytes], algorithms: list) -> dict:
    """여러 알고리즘으로 해시를 계산합니다."""
    results = {}

    for algorithm in algorithms:
        if algorithm in hashlib.algorithms_guaranteed:
            results[algorithm] = calculate_data_hash(data, algorithm)
        else:
            print(f"지원되지 않는 알고리즘: {algorithm}")

    return results


def create_checksum_file(file_path: Union[str, Path], checksum_filename: Optional[str] = None, algorithm: str = 'sha256') -> Optional[Path]:
    """체크섬 파일을 생성합니다."""
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        file_hash = calculate_file_hash(file_path, algorithm)

        if not file_hash:
            return None

        # 체크섬 파일명 결정
        if checksum_filename:
            checksum_path = file_path.parent / checksum_filename
        else:
            checksum_path = file_path.with_suffix(
                f"{file_path.suffix}.{algorithm}")

        # 체크섬 파일 작성
        with open(checksum_path, 'w', encoding='utf-8') as f:
            f.write(f"{file_hash}  {file_path.name}\n")

        return checksum_path

    except Exception as e:
        print(f"체크섬 파일 생성 오류: {e}")
        return None


def verify_checksum_file(checksum_path: Union[str, Path]) -> dict:
    """체크섬 파일을 검증합니다."""
    try:
        checksum_path = Path(checksum_path)

        if not checksum_path.exists():
            return {'success': False, 'error': '체크섬 파일이 존재하지 않습니다.'}

        results = []

        with open(checksum_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 해시와 파일명 분리
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue

                expected_hash, filename = parts
                file_path = checksum_path.parent / filename

                if not file_path.exists():
                    results.append({
                        'filename': filename,
                        'status': 'missing',
                        'expected_hash': expected_hash,
                        'actual_hash': None
                    })
                    continue

                # 알고리즘 추정 (해시 길이로)
                algorithm = 'md5' if len(expected_hash) == 32 else 'sha256'
                actual_hash = calculate_file_hash(file_path, algorithm)

                results.append({
                    'filename': filename,
                    'status': 'verified' if actual_hash.lower() == expected_hash.lower() else 'mismatch',
                    'expected_hash': expected_hash,
                    'actual_hash': actual_hash
                })

        return {'success': True, 'results': results}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def quick_hash(text: str, length: int = 8) -> str:
    """빠른 해시 (짧은 식별자용)"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:length]

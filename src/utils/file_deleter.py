"""
물리적 파일 삭제 유틸리티

업로드 및 처리된 증거 파일을 디스크에서 삭제하는 기능 제공
"""

import shutil
from pathlib import Path
from typing import Dict, List
from ..core.SystemConfig import SystemConfig


def delete_physical_files(file_id: str, uploads_dir: str = None, processed_dir: str = None) -> Dict[str, any]:
    """
    파일 ID에 해당하는 모든 물리적 파일 삭제

    Args:
        file_id: 삭제할 파일 ID
        uploads_dir: 업로드 디렉터리 경로 (None이면 SystemConfig에서 가져옴)
        processed_dir: 처리된 파일 디렉터리 경로 (None이면 SystemConfig에서 가져옴)

    Returns:
        Dict: {
            'uploads_deleted': bool,
            'uploads_path': str,
            'evidence_deleted': bool,
            'evidence_folders': List[str],
            'errors': List[str]
        }
    """
    result = {
        'uploads_deleted': False,
        'uploads_path': None,
        'evidence_deleted': False,
        'evidence_folders': [],
        'errors': []
    }

    # 설정에서 경로 가져오기
    if uploads_dir is None:
        config = SystemConfig()
        uploads_dir = config.get('paths.uploads_dir', 'uploads')

    if processed_dir is None:
        config = SystemConfig()
        processed_dir = config.get('paths.processed_dir', 'processed_emails')

    # 1. uploads/ 디렉터리에서 파일 삭제
    try:
        uploads_path = Path(uploads_dir)
        if uploads_path.exists():
            for file_path in uploads_path.glob(f"{file_id}_*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        result['uploads_deleted'] = True
                        result['uploads_path'] = str(file_path)
                        print(f"✅ 업로드 파일 삭제: {file_path}")
                except Exception as e:
                    result['errors'].append(f"업로드 파일 삭제 실패 ({file_path}): {e}")
    except Exception as e:
        result['errors'].append(f"업로드 디렉터리 탐색 오류: {e}")

    # 2. processed_emails/ 디렉터리에서 증거 폴더 삭제
    try:
        processed_path = Path(processed_dir)
        if processed_path.exists():
            deleted_count = 0
            for folder_path in processed_path.iterdir():
                if folder_path.is_dir():
                    # 폴더 이름에 file_id가 포함되어 있는지 확인
                    # 예: [2021-01-13]_대표님_견적서_전달_해_드립니다 형태의 폴더명
                    # evidence/ 서브디렉터리 내부에서 file_id 검색
                    evidence_dir = folder_path / "evidence"
                    if evidence_dir.exists():
                        for evidence_file in evidence_dir.glob("*"):
                            # 파일명에 file_id가 포함되어 있으면 전체 폴더 삭제
                            if file_id in evidence_file.name or file_id in folder_path.name:
                                try:
                                    shutil.rmtree(folder_path)
                                    result['evidence_folders'].append(str(folder_path))
                                    deleted_count += 1
                                    print(f"✅ 증거 폴더 삭제: {folder_path}")
                                    break
                                except Exception as e:
                                    result['errors'].append(f"증거 폴더 삭제 실패 ({folder_path}): {e}")
                                    break

            if deleted_count > 0:
                result['evidence_deleted'] = True
    except Exception as e:
        result['errors'].append(f"처리된 파일 디렉터리 탐색 오류: {e}")

    return result


def delete_multiple_files(file_ids: List[str], uploads_dir: str = None, processed_dir: str = None) -> Dict[str, any]:
    """
    여러 파일을 한 번에 삭제

    Args:
        file_ids: 삭제할 파일 ID 리스트
        uploads_dir: 업로드 디렉터리 경로
        processed_dir: 처리된 파일 디렉터리 경로

    Returns:
        Dict: {
            'total': int,
            'success': int,
            'failed': int,
            'details': List[Dict]
        }
    """
    results = {
        'total': len(file_ids),
        'success': 0,
        'failed': 0,
        'details': []
    }

    for file_id in file_ids:
        result = delete_physical_files(file_id, uploads_dir, processed_dir)

        if result['uploads_deleted'] or result['evidence_deleted']:
            results['success'] += 1
        else:
            results['failed'] += 1

        results['details'].append({
            'file_id': file_id,
            'result': result
        })

    return results

"""
Bootstrap Icons를 Font Awesome으로 자동 변환하는 스크립트
MCP Desktop Commander로 효율적인 파일 처리
"""

import re
from pathlib import Path

# Bootstrap Icons → Font Awesome 매핑
ICON_MAPPING = {
    # 체크 & 확인
    "bi-shield-check": "fa-shield-alt",
    "bi-check-circle": "fa-check-circle",
    "bi-check-circle-fill": "fa-check-circle",
    "bi-check-square": "fa-check-square",

    # 정보 & 경고
    "bi-info-circle": "fa-info-circle",
    "bi-exclamation-triangle": "fa-exclamation-triangle",
    "bi-exclamation-circle": "fa-exclamation-circle",
    "bi-exclamation-triangle-fill": "fa-exclamation-triangle",
    "bi-exclamation-circle-fill": "fa-exclamation-circle",
    "bi-info-circle-fill": "fa-info-circle",
    "bi-x-circle-fill": "fa-times-circle",
    "bi-shield-exclamation": "fa-shield-alt",

    # 파일 & 문서
    "bi-file-earmark": "fa-file",
    "bi-file-earmark-text": "fa-file-alt",
    "bi-file-earmark-pdf": "fa-file-pdf",
    "bi-file-earmark-arrow-up": "fa-file-upload",
    "bi-file-earmark-check": "fa-file-check",
    "bi-file-earmark-plus": "fa-file-plus",
    "bi-file-earmark-code": "fa-file-code",
    "bi-file-text": "fa-file-alt",
    "bi-file": "fa-file",
    "bi-file-binary": "fa-file-code",
    "bi-files": "fa-copy",

    # 이메일
    "bi-envelope": "fa-envelope",
    "bi-envelope-open": "fa-envelope-open",
    "bi-envelope-paper": "fa-envelope",
    "bi-envelope-fill": "fa-envelope",

    # 업로드 & 다운로드
    "bi-upload": "fa-upload",
    "bi-download": "fa-download",
    "bi-cloud-upload": "fa-cloud-upload-alt",

    # 시간 & 히스토리
    "bi-clock": "fa-clock",
    "bi-clock-history": "fa-history",
    "bi-calendar-range": "fa-calendar",
    "bi-calendar": "fa-calendar",
    "bi-hourglass-split": "fa-hourglass-half",

    # 편집 & 삭제
    "bi-pencil": "fa-edit",
    "bi-trash": "fa-trash",
    "bi-x": "fa-times",

    # 보안
    "bi-lock-fill": "fa-lock",
    "bi-shield-check": "fa-shield-alt",

    # 목록 & 정렬
    "bi-list-ol": "fa-list-ol",
    "bi-list-ul": "fa-list-ul",
    "bi-list-task": "fa-tasks",
    "bi-list-timeline": "fa-stream",

    # 검색 & 보기
    "bi-search": "fa-search",
    "bi-eye": "fa-eye",

    # 화살표 & 네비게이션
    "bi-arrow-left": "fa-arrow-left",
    "bi-arrow-clockwise": "fa-sync",

    # 기타
    "bi-paperclip": "fa-paperclip",
    "bi-plus-circle": "fa-plus-circle",
    "bi-square": "fa-square",
    "bi-gear": "fa-cog",
    "bi-three-dots": "fa-ellipsis-v",
    "bi-camera": "fa-camera",
    "bi-clipboard-data": "fa-clipboard-list",
    "bi-graph-up": "fa-chart-line",
    "bi-box-arrow-up": "fa-file-export",
    "bi-link": "fa-link",
    "bi-inbox": "fa-inbox",
    "bi-book": "fa-book",
    "bi-percent": "fa-percent",
    "bi-folder-plus": "fa-folder-plus",
    "bi-folder2-open": "fa-folder-open",
    "bi-archive": "fa-archive",
    "bi-image": "fa-image",
    "bi-music-note": "fa-music",
    "bi-camera-video": "fa-video",
    "bi-table": "fa-table",
    "bi-easel": "fa-chalkboard",
    "bi-lightbulb": "fa-lightbulb",

    # 추가 매핑 (스타일 변형)
    "bi-plus": "fa-plus",
}


def convert_icon_class(match):
    """아이콘 클래스를 변환"""
    full_class = match.group(0)

    # bi bi-xxx 패턴 추출
    icon_match = re.search(r'bi bi-([\w-]+)', full_class)
    if not icon_match:
        return full_class

    bi_icon = f"bi-{icon_match.group(1)}"

    # 매핑에서 찾기
    if bi_icon in ICON_MAPPING:
        fa_icon = ICON_MAPPING[bi_icon]
        # bi bi-xxx를 fas fa-xxx로 교체
        return full_class.replace(f"bi bi-{icon_match.group(1)}", f"fas {fa_icon}")

    # 매핑에 없으면 원본 반환 (수동 확인 필요)
    print(f"⚠️  매핑 없음: {bi_icon}")
    return full_class


def convert_file(file_path: Path) -> tuple[int, list]:
    """파일의 아이콘을 변환"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # bi bi-로 시작하는 모든 패턴 찾기
    pattern = r'class="[^"]*\bbi\s+bi-[\w-]+[^"]*"'

    matches_before = len(re.findall(pattern, content))
    content = re.sub(pattern, convert_icon_class, content)
    matches_after = len(re.findall(pattern, content))

    converted_count = matches_before - matches_after

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return converted_count, []

    return 0, []


def main():
    """메인 함수"""
    templates_dir = Path(r"c:\dev\python-email\templates")

    target_files = [
        "index_new.html",
        "email_list_new.html",
        "email_detail.html",
        "admin_dashboard.html",
    ]

    src_templates = Path(r"c:\dev\python-email\src\web\templates")
    src_files = [
        "verify_integrity.html",
        "integrated_timeline.html",
        "add_evidence.html",
        "additional_evidence.html",
    ]

    print("🚀 Bootstrap Icons → Font Awesome 변환 시작\n")

    total_converted = 0

    # templates/ 디렉토리 처리
    for filename in target_files:
        file_path = templates_dir / filename
        if file_path.exists():
            converted, _ = convert_file(file_path)
            total_converted += converted
            print(f"✅ {filename}: {converted}개 변환")

    # src/web/templates/ 디렉토리 처리
    for filename in src_files:
        file_path = src_templates / filename
        if file_path.exists():
            converted, _ = convert_file(file_path)
            total_converted += converted
            print(f"✅ {filename}: {converted}개 변환")

    print(f"\n🎉 총 {total_converted}개 아이콘 변환 완료!")


if __name__ == "__main__":
    main()

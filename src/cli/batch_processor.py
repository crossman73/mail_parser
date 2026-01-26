# batch_processor.py
"""
대용량 또는 다중 mbox 파일을 배치로 처리하는 스크립트
"""

import argparse
import glob
import os
import sys
from datetime import datetime
from pathlib import Path


def find_mbox_files(directory: str, pattern: str = "*.mbox") -> list:
    """
    디렉토리에서 mbox 파일들을 찾습니다.
    """
    search_path = os.path.join(directory, pattern)
    mbox_files = glob.glob(search_path)
    return sorted(mbox_files)


def estimate_processing_time(file_size_mb: float) -> str:
    """
    파일 크기에 따른 예상 처리 시간을 계산합니다.
    """
    # 대략적인 추정: 1MB당 10초
    estimated_seconds = file_size_mb * 10

    if estimated_seconds < 60:
        return f"{estimated_seconds:.0f}초"
    elif estimated_seconds < 3600:
        return f"{estimated_seconds/60:.1f}분"
    else:
        return f"{estimated_seconds/3600:.1f}시간"


def get_file_info(filepath: str) -> dict:
    """
    파일 정보를 가져옵니다.
    """
    stat = os.stat(filepath)
    size_mb = stat.st_size / (1024 * 1024)

    return {
        'path': filepath,
        'filename': os.path.basename(filepath),
        'size_mb': size_mb,
        'estimated_time': estimate_processing_time(size_mb)
    }


def run_single_file(mbox_file: str, party: str, config: str, batch_output_dir: str) -> bool:
    """
    단일 mbox 파일을 처리합니다.
    """
    import subprocess

    # 파일별 출력 디렉토리 생성
    filename_base = os.path.splitext(os.path.basename(mbox_file))[0]
    file_output_dir = os.path.join(batch_output_dir, filename_base)

    # main.py 실행 명령 구성
    cmd = [
        sys.executable, 'main.py',
        mbox_file,
        '--party', party,
        '--config', config,
        '--select-emails', 'all',
        '--select-pdfs', 'all'
    ]

    print(f"\n🔄 처리 시작: {os.path.basename(mbox_file)}")
    print(f"명령: {' '.join(cmd)}")

    try:
        # 환경 변수에 OUTPUT_DIR 설정
        env = os.environ.copy()
        env['MAIL_PARSER_OUTPUT_DIR'] = file_output_dir

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"✅ 성공: {os.path.basename(mbox_file)}")
            return True
        else:
            print(f"❌ 실패: {os.path.basename(mbox_file)}")
            print(f"오류: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="다중 mbox 파일 배치 처리 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 디렉토리의 모든 mbox 파일 처리
  python batch_processor.py email_files/ --party 갑

  # 특정 패턴의 파일만 처리
  python batch_processor.py email_files/ --party 을 --pattern "case_*.mbox"

  # 사용자 정의 설정으로 처리
  python batch_processor.py email_files/ --party 갑 --config custom.json
        """
    )

    parser.add_argument("input_dir", help="mbox 파일들이 있는 디렉토리")
    parser.add_argument("--party", required=True, choices=['갑', '을'],
                        help="당사자 구분 ('갑' 또는 '을')")
    parser.add_argument("--config", default="config.json",
                        help="설정 파일 경로")
    parser.add_argument("--pattern", default="*.mbox",
                        help="파일 검색 패턴 (기본값: *.mbox)")
    parser.add_argument("--output-dir", default="batch_output",
                        help="배치 출력 디렉토리")
    parser.add_argument("--continue-on-error", action="store_true",
                        help="오류 발생 시에도 다음 파일 계속 처리")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 처리 없이 계획만 표시")

    args = parser.parse_args()

    print("="*60)
    print("📦 배치 처리 시스템")
    print("="*60)

    # 입력 디렉토리 확인
    if not os.path.exists(args.input_dir):
        print(f"❌ 입력 디렉토리를 찾을 수 없습니다: {args.input_dir}")
        return 1

    # 설정 파일 확인
    if not os.path.exists(args.config):
        print(f"❌ 설정 파일을 찾을 수 없습니다: {args.config}")
        return 1

    # mbox 파일들 찾기
    mbox_files = find_mbox_files(args.input_dir, args.pattern)

    if not mbox_files:
        print(
            f"⚠️  '{args.input_dir}'에서 '{args.pattern}' 패턴의 mbox 파일을 찾을 수 없습니다.")
        return 1

    print(f"\n📁 발견된 파일: {len(mbox_files)}개")
    print("─" * 40)

    # 파일 정보 표시
    total_size = 0
    file_infos = []

    for mbox_file in mbox_files:
        info = get_file_info(mbox_file)
        file_infos.append(info)
        total_size += info['size_mb']

        print(f"📄 {info['filename']}")
        print(f"   크기: {info['size_mb']:.1f}MB")
        print(f"   예상 시간: {info['estimated_time']}")

    print("─" * 40)
    print("📊 전체 요약:")
    print(f"   총 파일 수: {len(mbox_files)}개")
    print(f"   총 크기: {total_size:.1f}MB")
    print(f"   예상 총 처리 시간: {estimate_processing_time(total_size)}")

    # dry-run 모드
    if args.dry_run:
        print("\n🔍 DRY-RUN 모드: 실제 처리는 수행되지 않습니다.")
        print("\n처리 계획:")
        for i, info in enumerate(file_infos, 1):
            print(
                f"  {i}. {info['filename']} → {args.output_dir}/{Path(info['filename']).stem}/")
        return 0

    # 사용자 확인
    response = input("\n계속하시겠습니까? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("처리가 취소되었습니다.")
        return 0

    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)

    # 배치 처리 시작
    print(f"\n🚀 배치 처리 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*60)

    successful_files = []
    failed_files = []
    start_time = datetime.now()

    for i, mbox_file in enumerate(mbox_files, 1):
        print(f"\n[{i}/{len(mbox_files)}] 처리 중: {os.path.basename(mbox_file)}")

        success = run_single_file(
            mbox_file, args.party, args.config, args.output_dir)

        if success:
            successful_files.append(mbox_file)
        else:
            failed_files.append(mbox_file)

            if not args.continue_on_error:
                print("\n❌ 오류로 인해 배치 처리를 중단합니다.")
                print("--continue-on-error 옵션을 사용하면 오류를 무시하고 계속할 수 있습니다.")
                break

    # 최종 결과
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "="*60)
    print("📊 배치 처리 완료")
    print("="*60)
    print(f"⏱️  총 소요 시간: {duration}")
    print(f"✅ 성공: {len(successful_files)}개 파일")
    print(f"❌ 실패: {len(failed_files)}개 파일")

    if successful_files:
        print("\n✅ 성공한 파일들:")
        for file in successful_files:
            print(f"   • {os.path.basename(file)}")

    if failed_files:
        print("\n❌ 실패한 파일들:")
        for file in failed_files:
            print(f"   • {os.path.basename(file)}")

    print(f"\n📁 결과물은 '{args.output_dir}' 디렉토리에 저장되었습니다.")

    return 0 if not failed_files else 1


if __name__ == '__main__':
    sys.exit(main())

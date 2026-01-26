"""
이메일 증거 파서 메인 애플리케이션 - 통합 아키텍처 v2.0
"""
from ..core.unified_architecture import SystemConfig, UnifiedArchitecture
import argparse
import json
import os
import sys
from pathlib import Path

# 현재 파일의 부모 디렉터리를 sys.path에 추가
# 프로젝트 루트를 sys.path에 추가하여 `src.*` 절대 임포트가 작동하도록 함
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# 통합 아키텍처 임포트
from ..mail_parser.progress import (
    display_welcome_message,
    display_configuration_info,
    display_error_help,
    EmailProcessingProgress,
)
from ..mail_parser.processor import EmailEvidenceProcessor


def load_system_config(config_path: str = "config.json") -> SystemConfig:
    """시스템 설정 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        return SystemConfig(
            project_root=Path.cwd(),
            config_data=config_data,
            app_name="이메일 증거 처리 시스템",
            version="2.0.0",
            debug_mode=os.getenv('DEBUG', 'false').lower() == 'true'
        )
    except Exception as e:
        print(f"⚠️ 설정 파일 로드 실패, 기본 설정 사용: {e}")
        return SystemConfig(
            project_root=Path.cwd(),
            config_data={},
            app_name="이메일 증거 처리 시스템",
            version="2.0.0"
        )


def main():
    """메인 실행 함수 - 통합 아키텍처 기반"""
    parser = argparse.ArgumentParser(description="이메일 증거 파서 v2.0 - 통합 아키텍처")
    parser.add_argument("input_path", nargs='?', help="입력 파일 또는 폴더 경로")
    parser.add_argument("--output", "-o", default="output",
                        help="출력 디렉터리 (기본값: output)")
    parser.add_argument(
        "--config", "-c", default="config.json", help="설정 파일 경로")
    parser.add_argument("--timeline", "-t",
                        action="store_true", help="타임라인 생성")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    parser.add_argument("--web", "-w", action="store_true", help="웹 서버 시작")
    parser.add_argument("--port", "-p", type=int, default=5000, help="웹 서버 포트")
    parser.add_argument("--test", action="store_true", help="시스템 테스트 모드")

    args = parser.parse_args()

    # 시스템 설정 로드
    system_config = load_system_config(args.config)
    if args.verbose:
        system_config.debug_mode = True

    # 통합 아키텍처 초기화
    unified_arch = UnifiedArchitecture(system_config)

    try:
        # 시스템 초기화
        print("🚀 시스템 초기화 중...")
        unified_arch.initialize()

        # 웹 서버 모드
        if args.web:
            return start_web_server(unified_arch, args.port, args.verbose)

        # 테스트 모드
        if args.test:
            return run_system_test(unified_arch)

        # CLI 처리 모드
        if not args.input_path:
            print("❌ 오류: 입력 경로가 필요합니다. (--web 또는 --test 옵션 사용 가능)")
            print("\n사용 예시:")
            print(f"  python {sys.argv[0]} email_files/sample.mbox")
            print(f"  python {sys.argv[0]} --web --port 8080")
            print(f"  python {sys.argv[0]} --test")
            return 1

        return process_emails_cli(unified_arch, args)

    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        return 0
    except Exception as e:
        unified_arch.logger.error(f"시스템 오류: {e}")
        print(f"❌ 시스템 오류: {e}", file=sys.stderr)
        return 1
    finally:
        # 정리
        try:
            unified_arch.cleanup()
        except Exception:
            pass


def start_web_server(unified_arch: UnifiedArchitecture, port: int, verbose: bool):
    """웹 서버 시작"""
    try:
        from ..web.app import create_app

        # create_app expects an optional config path; pass minimal and attach
        # the unified architecture object to the app for downstream access.
        app = create_app()
        app.config['UNIFIED_ARCH'] = unified_arch

        print(f"🌐 웹 서버 시작 - http://localhost:{port}")
        print(f"📊 시스템 상태: http://localhost:{port}/system/status")
        print(f"🏥 헬스체크: http://localhost:{port}/health")
        print("⏹️ Ctrl+C로 종료")

        # Flask 실행
        app.run(
            host='0.0.0.0',
            port=port,
            debug=verbose,
            use_reloader=False  # 통합 아키텍처와 충돌 방지
        )

        return 0

    except ImportError as e:
        print(f"❌ 웹 서버 모듈 로드 실패: {e}")
        return 1
    except Exception as e:
        unified_arch.logger.error(f"웹 서버 시작 실패: {e}")
        print(f"❌ 웹 서버 시작 실패: {e}")
        return 1


def run_system_test(unified_arch: UnifiedArchitecture):
    """시스템 테스트 실행"""
    print("🧪 시스템 테스트 시작...")

    try:
        # 기본 테스트
        status = unified_arch.get_system_status()
        print(f"✅ 시스템 초기화: {status['app_name']} v{status['version']}")
        print(f"✅ 등록된 서비스: {len(status['registered_services'])}개")

        # 서비스 확인
        for service_name in status['registered_services']:
            try:
                service = unified_arch.get_service(service_name)
                print(f"  ✅ {service_name}: {type(service).__name__}")
            except Exception as e:
                print(f"  ❌ {service_name}: {e}")

        # 디렉터리 확인
        dirs = unified_arch.get_directories()
        print(f"✅ 디렉터리 설정: {len(dirs)}개")
        for name, path in dirs.items():
            exists = "존재" if path.exists() else "생성필요"
            print(f"  📁 {name}: {path} ({exists})")

        print("🎉 시스템 테스트 완료!")
        return 0

    except Exception as e:
        print(f"❌ 시스템 테스트 실패: {e}")
        return 1


def process_emails_cli(unified_arch: UnifiedArchitecture, args):
    """CLI 모드 이메일 처리"""
    try:
        # 이메일 프로세서 서비스 가져오기
        try:
            processor = unified_arch.get_service('email_processor')
        except Exception:
            # 서비스가 없으면 직접 생성 (Phase 2에서 개선 예정)
            from ..mail_parser.processor import EmailProcessor
            processor = EmailProcessor(unified_arch.config.config_data)

        print(f"📧 이메일 처리 시작: {args.input_path}")

        # 처리 실행
        results = processor.process_emails(args.input_path, args.output)
        unified_arch.logger.info(f"이메일 처리 완료: {len(results)}개")

        print(f"✅ 처리 완료: {len(results)}개 이메일")

        # 타임라인 생성 (옵션)
        if args.timeline:
            try:
                timeline_gen = unified_arch.get_service('timeline_generator')
            except Exception:
                from ..timeline_system.timeline_generator import \
                    TimelineGenerator
                timeline_gen = TimelineGenerator()

            timeline_gen.generate_timeline(results, args.output)
            print("✅ 타임라인 생성 완료")

        # 종합 보고서 생성
        try:
            from ..mail_parser.reporter import create_comprehensive_report
            report_path = create_comprehensive_report(results, args.output)
            print(f"✅ 종합 보고서 생성: {report_path}")
        except Exception as e:
            print(f"⚠️ 보고서 생성 실패: {e}")

        return 0

    except Exception as e:
        unified_arch.logger.error(f"CLI 처리 실패: {e}")
        print(f"❌ 처리 실패: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

OUTPUT_DIR = 'processed_emails'


def validate_arguments(args):
    """
    명령행 인수를 검증합니다.
    """
    errors = []

    # mbox 파일 존재 확인
    if not os.path.exists(args.mbox_file):
        errors.append(f"mbox 파일을 찾을 수 없습니다: '{args.mbox_file}'")

    # 설정 파일 존재 확인
    if not os.path.exists(args.config):
        errors.append(f"설정 파일을 찾을 수 없습니다: '{args.config}'")

    # 출력 디렉토리 쓰기 권한 확인
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        test_file = os.path.join(OUTPUT_DIR, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception:
        errors.append(f"출력 디렉토리에 쓰기 권한이 없습니다: '{OUTPUT_DIR}'")

    return errors


def parse_selection_argument(selection_str: str, max_count: int) -> list:
    """
    선택 인수를 파싱합니다.
    """
    if not selection_str:
        return []

    if selection_str.lower() == 'all':
        return list(range(1, max_count + 1))
    elif selection_str.lower() == 'none':
        return []

    try:
        indices = [int(x.strip()) for x in selection_str.split(',')]
        valid_indices = [idx for idx in indices if 1 <= idx <= max_count]

        if len(valid_indices) != len(indices):
            invalid_indices = [
                idx for idx in indices if idx not in valid_indices]
            print(f"⚠️  경고: 유효하지 않은 번호들이 무시됩니다: {invalid_indices}")

        return valid_indices
    except ValueError:
        raise ValueError(
            f"선택 인수 형식이 잘못되었습니다: '{selection_str}'. 예: '1,3,5' 또는 'all' 또는 'none'")


def main():
    try:
        display_welcome_message()

        parser = argparse.ArgumentParser(
            description="법원 제출용 메일박스 증거 처리 시스템",
            epilog="""
사용 예시:
  python main.py email.mbox --party 갑 --select-emails all --select-pdfs all
  python main.py email.mbox --party 을 --select-emails "1,3,5" --config custom.json
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument("mbox_file", help="처리할 mbox 파일 경로")
        parser.add_argument("--party", required=True, choices=['갑', '을'],
                            help="당사자 구분 ('갑' 또는 '을')")
        parser.add_argument("--config", default="config.json",
                            help="설정 파일 경로 (기본값: config.json)")
        parser.add_argument("--select-emails",
                            help="처리할 메일 선택 (예: '1,3,5', 'all', 'none')")
        parser.add_argument("--select-pdfs",
                            help="PDF로 변환할 파일 선택 (예: '1,3,5', 'all', 'none')")

        args = parser.parse_args()

        # 인수 검증
        validation_errors = validate_arguments(args)
        if validation_errors:
            print("\n❌ 입력 인수 오류:")
            for error in validation_errors:
                print(f"  • {error}")
            display_error_help("파일없음")
            return 1

        # 프로세서 초기화
        try:
            processor = EmailEvidenceProcessor(args.config)
            display_configuration_info(processor.config)
        except Exception as e:
            print(f"\n❌ 프로세서 초기화 실패: {str(e)}")
            display_error_help("설정오류", str(e))
            return 1

        # mbox 파일 로드
        try:
            processor.load_mbox(args.mbox_file)
        except Exception as e:
            print(f"\n❌ mbox 파일 로드 실패: {str(e)}")
            if "decode" in str(e).lower() or "encoding" in str(e).lower():
                display_error_help("인코딩오류", str(e))
            else:
                display_error_help("파일없음", str(e))
            return 1

        # 메일 목록 가져오기
        all_messages = processor.get_all_message_metadata()
        if not all_messages:
            print("\n⚠️  처리할 메일이 없습니다.")
            return 0

        print(f"\n📨 발견된 메일: {len(all_messages)}개")

        # 진행률 관리자 초기화
        progress = EmailProcessingProgress(len(all_messages))

        # 처리할 메일 선택
        progress.set_stage("메일 선택")

        try:
            if args.select_emails:
                selected_indices = parse_selection_argument(
                    args.select_emails, len(all_messages))
                selected_msg_ids = [all_messages[idx-1]['id']
                                    for idx in selected_indices]
            else:
                print("\n📋 사용 가능한 메일 목록:")
                for idx, msg in enumerate(all_messages[:10], 1):  # 처음 10개만 표시
                    print(f"  {idx:2d}. {msg['subject'][:50]}...")
                if len(all_messages) > 10:
                    print(f"  ... (총 {len(all_messages)}개)")

                print("\n처리할 메일을 선택하려면 --select-emails 옵션을 사용하세요.")
                print("예: --select-emails all (모든 메일)")
                print("예: --select-emails '1,3,5' (특정 메일)")
                return 0
        except ValueError as e:
            print(f"\n❌ {str(e)}")
            return 1

        if not selected_msg_ids:
            print("\n⚠️  선택된 메일이 없어 처리를 종료합니다.")
            return 0

        print(f"\n✅ 처리할 메일: {len(selected_msg_ids)}개")

        # 메일 처리
        progress.set_stage("메일 처리")
        processed_html_files = []

        try:
            for i, msg_id in enumerate(selected_msg_ids, 1):
                print(f"\n[{i}/{len(selected_msg_ids)}] 처리 중...")

                html_filepath = processor.process_single_message(
                    msg_id, OUTPUT_DIR)
                if html_filepath:
                    processed_html_files.append(html_filepath)
                    progress.update_email_processed()
                else:
                    progress.update_email_excluded()

        except KeyboardInterrupt:
            print("\n\n⚠️  사용자에 의해 중단되었습니다.")
            return 1
        except Exception as e:
            print(f"\n❌ 메일 처리 중 오류 발생: {str(e)}")
            if "memory" in str(e).lower() or "메모리" in str(e):
                display_error_help("메모리부족", str(e))
            else:
                display_error_help("처리오류", str(e))
            return 1

        print(f"\n✅ 메일 처리 완료: {len(processed_html_files)}개 파일 생성")

        # PDF 변환
        if processed_html_files and args.select_pdfs:
            progress.set_stage("PDF 변환")

            try:
                pdf_indices = parse_selection_argument(
                    args.select_pdfs, len(processed_html_files))
                selected_html_files = [
                    processed_html_files[idx-1] for idx in pdf_indices]
            except ValueError as e:
                print(f"\n❌ {str(e)}")
                return 1

            if selected_html_files:
                print(f"\n📄 PDF 변환 시작: {len(selected_html_files)}개 파일")

                evidence_number_counter = {args.party: 0}

                try:
                    for i, html_file in enumerate(selected_html_files, 1):
                        print(f"[{i}/{len(selected_html_files)}] PDF 변환 중...")
                        success = processor.convert_html_to_pdf(
                            html_file, args.party, evidence_number_counter)
                        if success:
                            progress.update_pdf_generated()

                except Exception as e:
                    print(f"\n❌ PDF 변환 중 오류 발생: {str(e)}")
                    return 1

                print(f"\n✅ PDF 변환 완료: {progress.pdf_generated}개 파일")

        # 최종 요약 출력
        progress.set_stage("완료")
        progress.display_summary()

        print(f"\n📁 결과물은 '{OUTPUT_DIR}' 디렉토리에 저장되었습니다.")
        print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  프로그램이 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        print("자세한 정보는 로그 파일을 확인하세요.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

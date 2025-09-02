#!/usr/bin/env python3
"""
통합 타임라인 생성 테스트
"""
from src.timeline.integrated_timeline_generator import \
    IntegratedTimelineGenerator
import os
import sys

sys.path.append('src')


def test_timeline_generation():
    """통합 타임라인 생성 테스트"""
    try:
        print("🔍 통합 타임라인 생성 테스트 시작...")

        # 생성기 초기화
        generator = IntegratedTimelineGenerator(
            base_dir=os.path.join(os.getcwd(), 'processed_emails')
        )

        print("✅ 생성기 초기화 완료")

        # 타임라인 생성
        print("📊 타임라인 생성 중...")
        timeline_result = generator.generate_integrated_timeline()

        print(f"✅ 타임라인 생성 완료!")
        print(f"📄 총 {len(timeline_result.timeline_items)}개의 타임라인 항목 생성")
        print(
            f"📅 기간: {timeline_result.start_date} ~ {timeline_result.end_date}")

        # 처음 5개 항목 출력
        print("\n📋 타임라인 항목 샘플 (처음 5개):")
        for i, item in enumerate(timeline_result.timeline_items[:5]):
            print(f"  {i+1}. [{item.event_date}] {item.title}")
            print(f"     구분: {item.type}, 중요도: {item.importance}")

        return True

    except Exception as e:
        print(f"❌ 타임라인 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_timeline_generation()
    if success:
        print("\n🎉 통합 타임라인 생성 테스트 성공!")
    else:
        print("\n💥 통합 타임라인 생성 테스트 실패!")

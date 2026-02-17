"""
점수 계산 유틸리티 모듈
"""


def calculate_statistics(results):
    """
    테스트 결과 통계 계산
    
    Args:
        results (list): 테스트 결과 리스트
    
    Returns:
        dict: 통계 정보
    """
    if not results:
        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "avg_scores": {},
            "avg_total_score": 0.0
        }
    
    total_tests = len(results)
    passed = sum(1 for r in results if r['evaluation']['pass'])
    failed = total_tests - passed
    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0.0
    
    # 항목별 평균 점수
    criteria_names = ["정확성", "관련성", "할루시네이션", "안전성", "스타일", "기능적_요건"]
    avg_scores = {}
    
    for criterion in criteria_names:
        scores = [r['evaluation']['scores'][criterion] for r in results]
        avg_scores[criterion] = sum(scores) / len(scores) if scores else 0.0
    
    # 전체 평균 점수
    total_scores = [r['evaluation']['total_score'] for r in results]
    avg_total_score = sum(total_scores) / len(total_scores) if total_scores else 0.0
    
    return {
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "avg_scores": avg_scores,
        "avg_total_score": avg_total_score
    }


def print_statistics(stats):
    """통계 정보 출력"""
    print("\n" + "="*80)
    print("📈 테스트 통계")
    print("="*80)
    print(f"총 테스트: {stats['total_tests']}개")
    print(f"통과 (PASS): {stats['passed']}개")
    print(f"실패 (FAIL): {stats['failed']}개")
    print(f"통과율: {stats['pass_rate']:.1f}%")
    print(f"평균 총점: {stats['avg_total_score']:.2f}/18점")
    print()
    print("항목별 평균 점수:")
    for criterion, score in stats['avg_scores'].items():
        bar = '█' * int(score) + '░' * (3 - int(score))
        print(f"  {criterion:12s} [{bar}] {score:.2f}/3점")
    print("="*80)


def calculate_category_statistics(results):
    """
    카테고리별 통계 계산
    
    Args:
        results (list): 테스트 결과 리스트
    
    Returns:
        dict: 카테고리별 통계
    """
    category_stats = {}
    
    for result in results:
        category = result['category']
        
        if category not in category_stats:
            category_stats[category] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "avg_score": 0.0,
                "scores": []
            }
        
        category_stats[category]["total"] += 1
        
        if result['evaluation']['pass']:
            category_stats[category]["passed"] += 1
        else:
            category_stats[category]["failed"] += 1
        
        category_stats[category]["scores"].append(result['evaluation']['total_score'])
    
    # 평균 점수 계산
    for category in category_stats:
        scores = category_stats[category]["scores"]
        category_stats[category]["avg_score"] = sum(scores) / len(scores) if scores else 0.0
    
    return category_stats


def print_category_statistics(category_stats):
    """카테고리별 통계 출력"""
    print("\n" + "="*80)
    print("📊 카테고리별 통계")
    print("="*80)
    
    for category, stats in category_stats.items():
        pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
        
        print(f"\n[{category}]")
        print(f"  총 테스트: {stats['total']}개")
        print(f"  통과: {stats['passed']}개 | 실패: {stats['failed']}개")
        print(f"  통과율: {pass_rate:.1f}%")
        print(f"  평균 점수: {stats['avg_score']:.2f}/18점")
    
    print("="*80)

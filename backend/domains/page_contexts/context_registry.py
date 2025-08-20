# context_registry.py
"""
모듈 설명: 
    - 각 페이지에 들어갈 컨텍스트를 관리하는 레지스트리
    - 페이지별로 필요한 데이터를 제공하는 함수들을 등록하고 관리한다.
주요 기능:
    -

작성자: KimDoYoung
작성일: 2025-08-07
버전: 1.0
"""

from backend.domains.page_contexts.context_files import files_tree, files_view


PAGE_CONTEXT_PROVIDERS = {
    "files/tree": files_tree,
    "files/view": files_view,
}

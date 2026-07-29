

def get_inline_query_results(offset: int, results: list, size: int = 50):
    overall_items = len(results)
    if offset >= overall_items:
        return []
    elif offset + size >= overall_items:
        return results[offset:overall_items + 1]
    else:
        return results[offset: offset + size]

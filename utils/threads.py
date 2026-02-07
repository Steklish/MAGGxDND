from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Any, List, Tuple

def run_in_parallel_args(
    func: Callable[..., Any],  # accepts *args
    arg_lists: Iterable[Tuple[Any, ...]],  # tuples of arguments
    n_workers: int = 5
) -> List[Any]:
    """Pass multiple args per task using tuples."""
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(func, *args_tuple) for args_tuple in arg_lists]
        return [f.result() for f in futures]
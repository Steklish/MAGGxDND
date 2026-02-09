from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Any, List, Sequence, Tuple

def run_in_parallel_args(
    func: Callable[..., Any],  # accepts *args
    arg_lists: Iterable[Tuple[Any, ...]],  # tuples of arguments
    n_workers: int = 5
) -> List[Any]:
    """Pass multiple args per task using tuples."""
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(func, *args_tuple) for args_tuple in arg_lists]
        return [f.result() for f in futures]
    
    
def run_list_in_parallel(
    funcs: Sequence[Callable[..., Any]],
    args_list: Sequence[Tuple[Any, ...]],
    n_workers: int = 5,
) -> List[Any]:
    """
    funcs[i] will be called as funcs[i](*args_list[i]).
    Results are returned in the same order as funcs/args_list.
    """
    if len(funcs) != len(args_list):
        raise ValueError("funcs and args_list must have the same length")

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        # submit in order
        futures = [
            executor.submit(func, *args)
            for func, args in zip(funcs, args_list)
        ]
        # collect results in the same order
        return [f.result() for f in futures]

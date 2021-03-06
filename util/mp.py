import itertools
import os
import warnings

import psutil

import libtbx.easy_mp


def available_cores() -> int:
    """
    Determine the number of available processor cores.

    There are a number of different methods to get this information, some of
    which may not be available on a specific OS and/or version of Python. So try
    them in order and return the first successful one.
    """

    nproc = os.environ.get("NSLOTS", 0)
    try:
        nproc = int(nproc)
        if nproc >= 1:
            return nproc
    except ValueError:
        pass

    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        pass

    try:
        return len(psutil.Process().cpu_affinity())
    except AttributeError:
        pass

    nproc = os.cpu_count()
    if nproc is not None:
        return nproc

    nproc = psutil.cpu_count()
    if nproc is not None:
        return nproc

    return 1


def parallel_map(
    func,
    iterable,
    processes=1,
    nslots=1,
    method=None,
    asynchronous=True,
    callback=None,
    preserve_order=True,
    preserve_exception_message=...,
    job_category="low",
):
    """
    A wrapper function to call either drmaa or easy_mp to do a parallel map
    calculation. This function is setup so that in each case we can select
    the number of cores on a machine
    """
    from dials.util.cluster_map import cluster_map as drmaa_parallel_map

    if preserve_exception_message is not Ellipsis:
        warnings.warn(
            "keyword argument 'preserve_exception_message' is deprecated",
            DeprecationWarning,
            stacklevel=2,
        )

    if method == "drmaa":
        return drmaa_parallel_map(
            func=func,
            iterable=iterable,
            callback=callback,
            nslots=nslots,
            njobs=processes,
            job_category=job_category,
        )
    else:
        qsub_command = "qsub -pe smp %d" % nslots
        return libtbx.easy_mp.parallel_map(
            func=func,
            iterable=iterable,
            callback=callback,
            method=method,
            processes=processes,
            qsub_command=qsub_command,
            asynchronous=asynchronous,
            preserve_order=preserve_order,
            preserve_exception_message=True,
        )


class __cluster_function_wrapper:
    """
    A function called by the multi node parallel map. On each cluster node, a
    nested parallel map using the multi processing method will be used.
    """

    def __init__(
        self,
        func,
        nproc=1,
        asynchronous=True,
        preserve_order=True,
        preserve_exception_message=...,
    ):
        self.func = func
        self.nproc = nproc
        self.asynchronous = asynchronous
        self.preserve_order = (preserve_order,)
        if preserve_exception_message is not Ellipsis:
            warnings.warn(
                "keyword argument 'preserve_exception_message' is deprecated",
                DeprecationWarning,
                stacklevel=2,
            )

    def __call__(self, iterable):
        return libtbx.easy_mp.parallel_map(
            func=self.func,
            iterable=iterable,
            processes=self.nproc,
            method="multiprocessing",
            asynchronous=self.asynchronous,
            preserve_order=self.preserve_order,
            preserve_exception_message=True,
        )


def _iterable_grouper(iterable, chunk_size):
    """
    Group the iterable into chunks of up to chunk_size items
    """
    args = [iter(iterable)] * chunk_size
    for group in itertools.zip_longest(*args):
        group = tuple(item for item in group if item is not None)
        yield group


class _iterable_wrapper:
    def __init__(self, function):
        self.__function = function

    def __call__(self, iterable):
        return [self.__function(item) for item in iterable]


def multi_node_parallel_map(
    func,
    iterable,
    njobs=1,
    nproc=1,
    cluster_method=None,
    asynchronous=True,
    callback=None,
    preserve_order=True,
    preserve_exception_message=...,
):
    """
    A wrapper function to call a function using multiple cluster nodes and with
    multiple processors on each node
    """
    if preserve_exception_message is not Ellipsis:
        warnings.warn(
            "keyword argument 'preserve_exception_message' is deprecated",
            DeprecationWarning,
            stacklevel=2,
        )

    # The function to all on the cluster
    cluster_func = __cluster_function_wrapper(
        func=func,
        nproc=nproc,
        asynchronous=asynchronous,
        preserve_order=preserve_order,
        preserve_exception_message=True,
    )

    # Create the cluster iterable
    cluster_iterable = _iterable_grouper(iterable, nproc)

    # Create the cluster callback
    if callback is not None:
        cluster_callback = _iterable_wrapper(callback)
    else:
        cluster_callback = None

    # Do the parallel map on the cluster
    result = parallel_map(
        func=cluster_func,
        iterable=cluster_iterable,
        callback=cluster_callback,
        method=cluster_method,
        nslots=nproc,
        processes=njobs,
        asynchronous=asynchronous,
        preserve_order=preserve_order,
    )

    # return result
    return [item for rlist in result for item in rlist]


def batch_multi_node_parallel_map(
    func=None,
    iterable=None,
    nproc=1,
    njobs=1,
    callback=None,
    cluster_method=None,
    chunksize=1,
):
    """
    A function to run jobs in batches in each process
    """
    # Call the batches in parallel
    return multi_node_parallel_map(
        func=_iterable_wrapper(func),
        iterable=_iterable_grouper(iterable, chunksize),
        nproc=nproc,
        njobs=njobs,
        cluster_method=cluster_method,
        callback=_iterable_wrapper(callback),
        preserve_order=True,
    )


if __name__ == "__main__":

    def func(x):
        return x

    iterable = list(range(100))

    multi_node_parallel_map(
        func,
        iterable,
        nproc=4,
        njobs=10,
        cluster_method="multiprocessing",
        callback=print,
    )

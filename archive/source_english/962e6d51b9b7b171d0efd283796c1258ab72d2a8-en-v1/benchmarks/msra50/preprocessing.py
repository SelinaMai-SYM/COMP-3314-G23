"""No preprocessing: the MSRA50 archive was not obtained."""


def preprocess(*_args, **_kwargs):
    raise RuntimeError(
        "MSRA50 preprocessing is not applied because the dataset is unavailable"
    )

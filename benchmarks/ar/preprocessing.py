"""No preprocessing: the AR archive was not obtained."""


def preprocess(*_args, **_kwargs):
    raise RuntimeError(
        "AR preprocessing is not applied because the dataset is unavailable"
    )

"""No preprocessing: the UMIST archive was not obtained."""


def preprocess(*_args, **_kwargs):
    raise RuntimeError(
        "UMIST preprocessing is not applied because the dataset is unavailable"
    )

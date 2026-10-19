"""No preprocessing: the BinAlpha archive was not obtained."""


def preprocess(*_args, **_kwargs):
    raise RuntimeError(
        "BinAlpha preprocessing is not applied because the dataset is unavailable"
    )

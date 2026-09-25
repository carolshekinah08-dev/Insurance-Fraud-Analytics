import pandas as pd


def optimize_memory(df):
    """Downcast numeric columns to reduce memory usage."""

    memory_before = (
        df.memory_usage(deep=True).sum() / 1024**2
    )

    print(
        f"Memory before optimization: "
        f"{memory_before:.2f} MB"
    )

    for col in df.columns:

        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = pd.to_numeric(
                df[col],
                downcast="integer"
            )

        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = pd.to_numeric(
                df[col],
                downcast="float"
            )

    memory_after = (
        df.memory_usage(deep=True).sum() / 1024**2
    )

    memory_saved = memory_before - memory_after

    print(
        f"Memory after optimization: "
        f"{memory_after:.2f} MB"
    )

    print(
        f"Memory saved: "
        f"{memory_saved:.2f} MB"
    )

    reduction = (
        memory_saved / memory_before
    ) * 100

    print(
        f"Memory reduction: "
        f"{reduction:.2f}%"
    )

    return df

    # Memory after optimization
    memory_after = (
        df.memory_usage(deep=True).sum() / 1024**2
    )

    print(
        f"Memory after optimization: "
        f"{memory_after:.2f} MB"
    )

    # Calculate savings
    memory_saved = memory_before - memory_after

    print(
        f"Memory saved: "
        f"{memory_saved:.2f} MB"
    )

    if memory_before > 0:
        percentage = (
            memory_saved / memory_before
        ) * 100

        print(
            f"Percentage reduction: "
            f"{percentage:.2f}%"
        )

    return df
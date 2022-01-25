from kedro.pipeline import Pipeline, node

from .nodes import training_loop


def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=training_loop,
                inputs=[
                    "train_sequences",
                    "val_sequences",
                    "test_sequences",
                    "params:training",
                ],
                outputs=None,
                name="training_model_node",
            ),
        ]
    )
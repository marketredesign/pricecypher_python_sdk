from dataclasses import dataclass

type Models = dict[str, Model]

@dataclass(frozen=True)
class Model:
    """Defines a (trained) model.

    model (object): The trained model.
    model_details (dict): A dict with model details.
    """
    model: object
    model_details: dict

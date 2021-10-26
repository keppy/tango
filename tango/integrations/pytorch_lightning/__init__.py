"""
Components for Tango integration with `PyTorch Lightning <https://www.pytorchlightning.ai/>`_.

.. important::
    To use this integration you should install ``tango`` with the "pytorch_lightning" extra
    (e.g. ``pip install tango[pytorch_lightning]``) or just install PyTorch Lightning after the fact.

These include a basic training loop :class:`~tango.step.Step` and registrable versions
of ``pytorch_lightning`` classes, such as :class:`pytorch_lightning.LightningModule`, :class:`pytorch_lightning.Callback`, etc.

Example: training a model
-------------------------

Let's look a simple example of training a model.

We'll make a very basic regression model and generate some fake data to train on.
First, the setup:

.. testcode::

    import torch
    import torch.nn as nn

    from tango.common.dataset_dict import DatasetDict
    from tango.step import Step
    from tango.integrations.pytorch_lightning import LightningModule

Now let's build and register our model:

.. testcode::

    @LightningModule.register("basic_regression")
    class BasicRegression(LightningModule):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(10, 1)
            self.sigmoid = nn.Sigmoid()
            self.mse = nn.MSELoss()

        def forward(self, x, y=None):
            pred = self.sigmoid(self.linear(x))
            out = {"pred": pred}
            if y is not None:
                out["loss"] = self.mse(pred, y)
            return out

        def _to_params(self):
            return {}

        def training_step(self, batch, batch_idx):
            outputs = self.forward(**batch)
            return outputs["loss"]

        def validation_step(self, batch, batch_idx, dataloader_idx=0):
            outputs = self.forward(**batch)
            return outputs

        def configure_optimizers(self):
            optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
            return optimizer

Lastly, we'll need a step to generate data:

.. testcode::

    @Step.register("generate_data")
    class GenerateData(Step):
        DETERMINISTIC = True
        CACHEABLE = False

        def run(self) -> DatasetDict:
            torch.manual_seed(1)
            return DatasetDict(
                {
                    "train": [{"x": torch.rand(10), "y": torch.rand(1)} for _ in range(64)],
                    "validation": [{"x": torch.rand(10), "y": torch.rand(1)} for _ in range(32)],
                }
            )

You could then run this experiment with a config that looks like this:

.. literalinclude:: ../../../../test_fixtures/integrations/pytorch_lightning/train.jsonnet

.. testcode::
    :hide:

    from tango.common.testing import run_experiment
    from tango.common.registrable import Registrable

    # Don't cache results, otherwise we'll have a pickling error.
    with run_experiment(
        "test_fixtures/integrations/pytorch_lightning/train.jsonnet",
        overrides="{'steps.train.cache_results':false}"
    ) as run_dir:
        assert (run_dir / "step_cache").is_dir()
    # Restore state of registry.
    del Registrable._registry[Step]["generate_data"]
    del Registrable._registry[LightningModule]["basic_regression"]

For example,

.. code-block::

    tango run train.jsonnet -i my_package -d /tmp/train

would produce the following output:

.. testoutput::

    Starting run for "data"...
    Finished run for "data"

    Starting run for "train"...
    <Epochs log>
    Finished run for "train"

Tips
----

PyTorch Lightning functionality
~~~~~~~~~~~~~~~~

You can use existing Pytorch Lightning callbacks, loggers, and profilers, which are registered as
"pytorch_lightning::<callback, logger, or profiler name>".

"""

__all__ = [
    "LightningAccelerator",
    "LightningCallback",
    "LightningLogger",
    "LightningModule",
    "LightningProfiler",
    "LightningTrainStep",
]

from .accelerators import LightningAccelerator
from .callbacks import LightningCallback
from .loggers import LightningLogger
from .model import LightningModule
from .profilers import LightningProfiler
from .train import LightningTrainStep

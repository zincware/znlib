import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import to_categorical
from zntrack import Node, dvc, utils, zn


class DataPreprocessor(Node):
    """Prepare dataset for training
    * normalize and reshape the features
    * one-hot encode the labels
    """

    data: pathlib.Path = dvc.deps()

    # outputs
    features: np.ndarray = zn.outs()
    labels: np.ndarray = zn.outs()

    def run(self):
        """Primary Node Method"""
        df = pd.read_csv(self.data)

        # one hot encode the labels
        self.labels = df.values[:, 0]
        self.labels = to_categorical(self.labels)
        self.features = df.values[:, 1:]

        # normalize and scale the features
        self.features = self.features / 255
        self.features = self.features.reshape((-1, 28, 28, 1))

    def plot(self, index):
        """Plot a single image of the dataset"""
        plt.imshow(self.features[index])
        plt.title(f"Label {self.labels[index].argmax()}")
        plt.show()


class Conv2DModel(Node):
    """Train a convolutional 2D model on the training dataset"""

    # dependencies
    train_data: DataPreprocessor = zn.deps()

    # outputs
    model_path: pathlib.Path = dvc.outs(utils.nwd / "model")

    training_history = zn.plots(x="epoch", y="val_accuracy")
    metrics = zn.metrics()

    # parameter
    epochs = zn.params()
    filters = zn.params([4, 4])
    dense = zn.params([64, 32])
    optimizer = zn.params("adam")

    model: keras.Model = None

    def post_init(self):
        """Load the model if possible"""
        if self.is_loaded and self.model_path.exists():
            self.model = keras.models.load_model(self.model_path)

    def run(self):
        """Primary Node Method"""
        self.build_model()
        self.train_model()
        self.model.save(self.model_path)

    def train_model(self):
        """Train the model"""
        self.model.compile(
            optimizer=self.optimizer,
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        print(self.model.summary())

        history = self.model.fit(
            self.train_data.features,
            self.train_data.labels,
            validation_split=0.3,
            epochs=self.epochs,
            batch_size=64,
        )
        self.training_history = pd.DataFrame(history.history)
        self.training_history.index.name = "epoch"
        # use the last values for model metrics
        self.metrics = dict(self.training_history.iloc[-1])

    def build_model(self):
        """Build the model using keras.Sequential API"""

        inputs = keras.Input(shape=(28, 28, 1))
        cargo = inputs
        for filters in self.filters:
            cargo = layers.Conv2D(
                filters=filters, kernel_size=(3, 3), padding="same", activation="relu"
            )(cargo)
            cargo = layers.MaxPooling2D((2, 2))(cargo)

        cargo = layers.Flatten()(cargo)

        for dense in self.dense:
            cargo = layers.Dense(dense, activation="relu")(cargo)

        output = layers.Dense(25, activation="softmax")(cargo)

        self.model = keras.Model(inputs=inputs, outputs=output)


class EvaluateModel(Node):
    """Evaluate the Model on a given test dataset"""

    # dependencies
    model: Conv2DModel = zn.deps()
    test_data = zn.deps()
    # metrics
    metrics = zn.metrics()
    confusion_matrix = zn.plots(template="confusion", x="predicted", y="actual")

    def run(self):
        """Primary Node Method"""
        loss, accuracy = self.model.model.evaluate(
            self.test_data.features, self.test_data.labels
        )
        self.metrics = {"loss": loss, "accuracy": accuracy}

        prediction = self.model.model.predict(self.test_data.features)

        self.confusion_matrix = pd.DataFrame(
            [
                {"actual": np.argmax(true), "predicted": np.argmax(false)}
                for true, false in zip(self.test_data.labels, prediction)
            ]
        )

    def plot_confusion_matrix(self):
        """Plot the confusion matrix based on the evaluation of the test data"""
        cf_mat = confusion_matrix(
            self.confusion_matrix["actual"], self.confusion_matrix["predicted"]
        )
        plt.imshow(cf_mat)


def build_workflow():
    """Build a workflow based to train the sign_language_mnist dataset

    References
    ----------
    The dataset is available at
     https://www.kaggle.com/datasets/datamunge/sign-language-mnist
    """
    train_data = DataPreprocessor(data="sign_mnist_train.csv", name="train")
    train_data.write_graph()

    test_data = DataPreprocessor(data="sign_mnist_test.csv", name="test")
    test_data.write_graph()

    model = Conv2DModel(train_data=train_data, epochs=30)
    model.write_graph()

    evaluate = EvaluateModel(model=model, test_data=test_data)
    evaluate.write_graph()

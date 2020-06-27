import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import layers
from keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from tensorflow import keras
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
from dataset import dataset_windowed


class FFNN(tf.keras.Model):
    def __init__(self, output_dim):
        super(FFNN, self).__init__()
        self.hidden1 = tf.keras.layers.Dense(20, activation=tf.nn.elu)
        self.hidden2 = tf.keras.layers.Dense(20, activation=tf.nn.elu)
        self.hidden3 = tf.keras.layers.Dense(15, activation=tf.nn.elu)
        # self.dropout1 = tf.keras.layers.Dropout(0.7)
        # self.dropout2 = tf.keras.layers.Dropout(0.5)
        # self.dropout3 = tf.keras.layers.Dropout(0.5)
        # self.batchnorm = tf.keras.layers.BatchNormalization(momentum=0.999)
        self.last = tf.keras.layers.Dense(output_dim, activation=tf.nn.softmax)

    def call(self, inputs, training=False):
        x = self.hidden1(inputs)
        # if training:
        #     x = self.dropout1(x)
        # x = self.batchnorm(x)
        x = self.hidden2(x)
        # if training:
        #     x = self.dropout2(x)
        x = self.hidden3(x)
        # if training:
        #     x = self.dropout3(x)
        return self.last(x)


if __name__ == "__main__":
    tf.keras.backend.set_floatx("float64")
    # load and split the dataset
    ds = dataset_windowed(N=100000, K=300)
    ingress = (
        ds["packets_length_total"]
        .map(np.array)
        .map(lambda l: l[l > 0])
        .where(lambda s: s.map(lambda l: l.size) > 0)
        .dropna()
    )
    ds["packets_length_mean"] = ingress.map(np.mean)
    ds["packets_length_std"] = ingress.map(np.std)
    ds = ds.drop(columns=["packets_length_total"]).dropna()

    X_train, X_test, y_train, y_test = train_test_split(
        ds.drop("app", axis=1),
        ds["app"].astype("category"),
        test_size=0.2,
        # train_size=0.2,
        random_state=1234,
    )
    print("X_train size: ", X_train.shape)
    print("X_test size: ", X_test.shape)

    # generate labels that Keras can understand
    y_train_dumm, y_test_dumm = pd.get_dummies(y_train), pd.get_dummies(y_test)

    # generation of the model
    model = FFNN(len(ds["app"].unique()))

    model.compile(
        loss="categorical_crossentropy", optimizer="Adamax", metrics=["accuracy"]
    )

    history = model.fit(x=X_train, y=y_train_dumm, epochs=30, batch_size=100)

    model.summary()
    fig, ax_left = plt.subplots()
    ax_left.set_xlabel("epoch")
    ax_left.set_ylabel("loss", color="tab:red")
    ax_left.plot(history.history["loss"], color="tab:red")
    ax_left.tick_params(axis="y", labelcolor="tab:red")
    ax_right = ax_left.twinx()
    ax_right.set_ylabel("accuracy", color="tab:blue")
    ax_right.plot(history.history["accuracy"], color="tab:blue")
    ax_right.tick_params(axis="y", labelcolor="tab:blue")

    # evaluation on test set
    loss, acc = model.evaluate(X_test, y_test_dumm, batch_size=100)
    print(f"loss: {loss}")
    print(f"acc: {acc}")

    y_pred_dumm = pd.DataFrame(
        model.predict(X_test, batch_size=100), columns=y_test_dumm.columns,
    )
    y_pred = y_pred_dumm.idxmax(axis="columns").astype("category")

    cm = tf.math.confusion_matrix(
        labels=y_test.cat.codes, predictions=y_pred.cat.codes
    ).numpy()
    disp = ConfusionMatrixDisplay(cm, display_labels=y_test_dumm.columns)
    disp.plot()
    plt.show()

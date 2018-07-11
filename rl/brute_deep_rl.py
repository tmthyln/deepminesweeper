import tensorflow as tf
from tensorflow import layers as tl

from rl.agent import Agent


class DeepImitationAgent(Agent):
    def __init__(self, mode):
        assert mode in ['training', 'inference']

        self.mode = mode
        self.sess = tf.Session()

        self._build()

    def _build(self):
        self.invisible_sites = tf.placeholder(shape=(None, None, 1), dtype=tf.float32)
        self.open_sites = tf.placeholder(shape=(None, None, 1), dtype=tf.float32)
        self.proximity_matrix = tf.placeholder(shape=(None, None, 1), dtype=tf.float32)

        if self.mode == 'training':
            self.gt_coordinates = tf.placeholder(shape=(2,), dtype=tf.float32)

        x = tl.conv2d(tf.expand_dims(self.proximity_matrix, axis=0),
                      8, (3, 3), padding='same', activation=tf.nn.relu6)
        x = tf.concat((tf.expand_dims(self.invisible_sites, axis=0),
                       tf.expand_dims(self.open_sites, axis=0), x), axis=3)

        x = tl.conv2d(x, 8, (3, 3), activation=tf.nn.relu6)
        x = tl.conv2d(x, 8, (3, 3), activation=tf.nn.relu6)
        x = tl.max_pooling2d(x, (2, 2), (2, 2))

        x = tl.conv2d(x, 16, (3, 3), activation=tf.nn.relu6)
        x = tl.conv2d(x, 16, (3, 3), activation=tf.nn.relu6)
        x = tl.max_pooling2d(x, (2, 2), (2, 2))

        x = tl.conv2d(x, 32, (3, 3), activation=tf.nn.relu6)
        x = tl.conv2d(x, 32, (3, 3), activation=tf.nn.relu6)
        x = tl.max_pooling2d(x, (2, 2), (2, 2))

        x = tl.conv2d(x, 64, (3, 3), activation=tf.nn.relu6)
        x = tl.conv2d(x, 64, (3, 3), activation=tf.nn.relu6)
        x = tl.max_pooling2d(x, (2, 2), (2, 2))

        x = tl.conv2d(x, 128, (3, 3), activation=tf.nn.relu6)
        x = tl.conv2d(x, 128, (3, 3), activation=tf.nn.relu6)
        x = tl.conv2d(x, 2, (1, 1), activation=tf.nn.relu6)
        x = tl.max_pooling2d(x, (2, 2), (2, 2))

        x = tf.reduce_mean(x, axis=(0, 1, 2))
        x = tf.sigmoid(x)

        self.coordinates = x

        if self.mode == 'training':
            self.loss = tf.losses.mean_squared_error(self.gt_coordinates, self.coordinates)
            self.optimizer = tf.train.AdadeltaOptimizer().minimize(self.loss)

    def think(self, visibility_matrix, proximity_matrix):
        inputs = {
            self.invisible_sites: visibility_matrix[..., 1],
            self.open_sites: visibility_matrix[..., 2],
            self.proximity_matrix: proximity_matrix}

        coords = self.sess.run(self.coordinates, feed_dict=inputs)

        rows, cols = proximity_matrix.shape

        return rows * coords[0], cols * coords[1]

    def feedback(self, reward):
        pass

    def train(self, visibility_matrix, proximity_matrix, gt_coordinates):
        inputs = {
            self.invisible_sites: visibility_matrix[..., 1],
            self.open_sites: visibility_matrix[..., 2],
            self.proximity_matrix: proximity_matrix,
            self.gt_coordinates: gt_coordinates}

        _, loss, _ = self.sess.run((self.coordinates, self.loss, self.optimizer), feed_dict=inputs)

        return loss


def train_brute_deep_rl_agent():
    pass


agent = DeepImitationAgent('training')


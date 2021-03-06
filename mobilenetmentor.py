import tensorflow as tf 
tf.set_random_seed(1234)
from tensorflow.python.framework import ops
from tensorflow.python.framework import dtypes
import random
import numpy as np
np.random.seed(1234)
#from tensorflow.contrib.keras.python.keras.applications.mobilenet import _conv_block, _depthwise_conv_block
from tensorflow.contrib.keras.python.keras.applications.mobilenet import DepthwiseConv2D
from tensorflow.contrib.keras.python.keras.layers import GlobalAveragePooling2D
from tensorflow.contrib.keras.python.keras.models import Model
from tensorflow.contrib.keras.python.keras.layers import Input
from tensorflow.contrib.keras.python.keras.layers import Dense
from tensorflow.contrib.keras.python.keras.layers import Dropout
from tensorflow.contrib.keras.python.keras.layers import Conv2D
from tensorflow.contrib.keras.python.keras.layers import Reshape
from tensorflow.contrib.keras.python.keras.layers import add
from tensorflow.contrib.keras.python.keras.layers import Activation, Flatten, MaxPooling2D,BatchNormalization
from tensorflow.contrib.keras.python.keras.layers import GaussianNoise 
from tensorflow.contrib.keras.python.keras.losses import categorical_crossentropy
from tensorflow.contrib.keras.python.keras import backend as K
from tensorflow.contrib.keras.python.keras.models import Sequential
import pdb
depth_multiplier = 1
class Mentor(object):

    def __init__(self, trainable, num_classes):
        self.trainable = trainable
        self.num_classes = num_classes

    def relu6(self, x):
        return K.relu(x, max_value=6)

    def build(self,alpha, img_input, temp_softmax):

        shape = (1, 1, int(1024 * alpha))
	"""
	This looks dangerous. Not sure how the model would get affected with the laarning_phase variable set to True.
	"""
        
        K.set_learning_phase(True)

	with tf.name_scope('teacher') as scope:

	    self.conv1 = Conv2D(
                        int(32*alpha),
                        (3,3),
                        padding='same',
                        use_bias=False,
                        strides=(1,1),
                        name='teacher_conv1', trainable=self.trainable)(img_input)
            self.conv2 = BatchNormalization(axis=-1, name='teacher_conv1_bn', trainable=self.trainable)(self.conv1)
            self.conv3 = Activation(self.relu6, name='teacher_conv1_relu', trainable=self.trainable)(self.conv2)

	    self.conv4 = self._depthwise_conv_block(self.conv3, 64, alpha, depth_multiplier, block_id = 15)
	    self.conv5 = self._depthwise_conv_block(self.conv4, 128, alpha, depth_multiplier,strides=(2, 2), block_id =16)
	    self.conv6 =self. _depthwise_conv_block(self.conv5, 128, alpha, depth_multiplier,block_id =17)
	    self.conv7 = self._depthwise_conv_block(self.conv6, 256, alpha, depth_multiplier, strides=(2,2),block_id =18)
	    self.conv8 = self._depthwise_conv_block(self.conv7, 256, alpha, depth_multiplier, block_id =19)
	    self.conv9 = self._depthwise_conv_block(self.conv8, 512, alpha, depth_multiplier, strides = (2,2), block_id =20)
	    self.conv10 = self._depthwise_conv_block(self.conv9, 512, alpha, depth_multiplier, block_id =21)
	    self.conv11 = self._depthwise_conv_block(self.conv10, 512, alpha, depth_multiplier, block_id =22)
	    self.conv12 = self._depthwise_conv_block(self.conv11, 512, alpha, depth_multiplier, block_id =23)
	    self.conv13 = self._depthwise_conv_block(self.conv12, 512, alpha, depth_multiplier, block_id =24)
	    self.conv14 = self._depthwise_conv_block(self.conv13, 512, alpha, depth_multiplier, block_id =25)
	    self.conv15 = self._depthwise_conv_block(self.conv14, 1024, alpha, depth_multiplier,strides=(2,2), block_id =26)
	    self.conv16 = self._depthwise_conv_block(self.conv15, 1024, alpha, depth_multiplier, block_id =27)

            self.conv17 = GlobalAveragePooling2D()(self.conv16)
            self.conv18 = Reshape(shape, name='teacher_reshape_1', trainable=self.trainable)(self.conv17)
	
            self.conv19 = Dropout(0.5, name='teacher_dropout', trainable=self.trainable)(self.conv18)
            self.conv20 = Conv2D(self.num_classes, (1, 1), padding='same', name='teacher_conv_preds', trainable=self.trainable)(self.conv18)
            self.conv21 = Activation('softmax', name='teacher_act_softmax', trainable=self.trainable)(tf.divide(self.conv20, temp_softmax))
            self.conv22 = Reshape((self.num_classes,), name='teacher_reshape_2', trainable=self.trainable)(self.conv21)

        return self
    def loss(self, labels):
        labels = tf.to_int64(labels)
        """
            softmax cross entropy with logits takes logits as input instead of probabilities. check the input for caution.
        """

        logits = Reshape((self.num_classes,), name='teacher_reshape_3', trainable=self.trainable)(self.conv20)
        cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels = labels, logits = logits, name='xentropy')
        return tf.reduce_mean(cross_entropy, name='xentropy_mean')

    def training(self, loss, lr, global_step):
        tf.summary.scalar('loss', loss)
        optimizer = tf.train.AdamOptimizer(lr)
        train_op = optimizer.minimize(loss, global_step=global_step)

        return train_op
    def _depthwise_conv_block(self, inputs, pointwise_conv_filters, alpha,depth_multiplier=1, strides=(1, 1), block_id=1):
        pointwise_conv_filters = int(pointwise_conv_filters * alpha)
    	x = DepthwiseConv2D((3, 3),
			    padding='same',
			    depth_multiplier=depth_multiplier,
			    strides=strides,
			    use_bias=False,
			    name='teacher_conv_dw_%d' % block_id, trainable=self.trainable)(inputs)
	x = BatchNormalization(axis=-1, name='teacher_conv_dw_%d_bn' % block_id, trainable=self.trainable)(x)
	x = Activation(self.relu6, name='teacher_conv_dw_%d_relu' % block_id, trainable=self.trainable)(x)

	x = Conv2D(pointwise_conv_filters, (1, 1),
		   padding='same',
		   use_bias=False,
		   strides=(1, 1),
		   name='teacher_conv_pw_%d' % block_id, trainable=self.trainable)(x)
	x = BatchNormalization(axis=-1, name='teacher_conv_pw_%d_bn' % block_id, trainable=self.trainable)(x)
        return Activation(self.relu6, name='teacher_conv_pw_%d_relu' % block_id, trainable=self.trainable)(x)


""" Bayesian Network """
import numpy as np
import paddle
import paddle.fluid as fluid


class BayesianNet(paddle.nn.Layer):
    """
    We currently support 3 types of variables: x = observation, z = latent, y = condition.
    A Bayeisian Network models a generative process for certain varaiables: p(x,z|y) or p(z|x,y) or p(x|z,y)
    """
    def __init__(self):
        super(BayesianNet, self).__init__()
        self._nodes = {}
        self._cache = {}

    @property
    def nodes(self):
        return self._nodes

    @property
    def cache(self):
        return self._nodes

    def Normal(self,
               name,
               nodes,
               observation=None,
               mean=None,
               std=None,
               seed=0,
               dtype='float32',
               shape=(),
               reparameterize=True):

        """ Normal distribution wrapper """

        assert not name is None
        assert not nodes is None
        assert not seed is None
        assert not dtype is None

        if name in observation.keys():
            sample = observation[name]
        else:
        #if observation is None:
            if reparameterize:
                epsilon = paddle.normal(name='sample', shape=fluid.layers.shape(std), mean=0.0, std=1.0)
                sample = mean + std * epsilon
                # epsilon = self.normal_dist('sample', shape, self.zeros(mean.shape), self.ones(std.shape))
                # sample = mean + std * epsilon
            else:
                sample = paddle.normal(name='sample', \
                                       shape=fluid.layers.shape(std), mean=0.0, std=1.0) * std + mean
                # sample = fluid.layers.gaussian_random(name='sample', shape=fluid.layers.shape(std)) * std + mean
                # sample = self.normal_dist('sample', shape, mean, std)
        # else:
        #     sample = observation

        ## Log Prob
        logstd = paddle.log(std)
        c = -0.5 * np.log(2 * np.pi)
        precision = paddle.exp(-2 * logstd)
        # print([sample.shape, mean.shape, logstd.shape, precision.shape])
        log_prob_sample = c - logstd - 0.5 * precision * paddle.square(sample - mean)

        log_prob = fluid.layers.reduce_sum(log_prob_sample, dim=1)
        
        nodes[name] = (sample, log_prob)
        #print('sample shape:' , sample.shape)
        #print('log_prob shape:' , log_prob.shape)
        assert([sample.shape[0]] == log_prob.shape)
        return nodes #sample, log_prob

    def Bernoulli(self,
                  name,
                  nodes,
                  observation=None,
                  probs=None,
                  seed=0,
                  dtype='float32',
                  shape=()):
        """ Bernoulli distribution wrapper """

        assert not name is None
        assert not nodes is None
        assert not seed is None
        assert not dtype is None

        #print(observation.keys())
        if name in observation.keys():
            sample = observation[name]
        else:
        # if observation is None:
            sample = paddle.bernoulli(probs)
            # sample = self.bernoulli_dist('sample', shape, probs)
        # else:
        #     sample = observation

        ## Log Prob
        # print(sample.keys())
        #logits = paddle.log(probs /(1-probs))
        #log_prob_sample = -fluid.layers.sigmoid_cross_entropy_with_logits(label=sample, x=logits) # check mark

        log_prob_sample = sample * paddle.log(probs + 1e-8) + (1 - sample) * paddle.log(1 - probs + 1e-8)

        log_prob = fluid.layers.reduce_sum(log_prob_sample, dim=1)

        nodes[name] = (sample, log_prob)
        assert([sample.shape[0]] == log_prob.shape)
        return nodes #sample, log_prob


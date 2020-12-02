import paddle
import paddle.fluid as fluid

from .base import Distribution

class Bernoulli(Distribution):
    def __init__(self,
                 dtype='float32',
                 param_dtype='float32',
                 is_continues=False,
                 is_reparameterized=True,
                 group_ndims=0,
                 **kwargs):
        super(Bernoulli, self).__init__(dtype, 
                             param_dtype, 
                             is_continues,
                             is_reparameterized,
                             group_ndims=group_ndims,
                             **kwargs)
        self._probs = kwargs['probs']

    @property
    def probss(self):
        """The odds of probabilities of being 1."""
        return self._probs


    def _sample(self, n_samples=1, **kwargs): 
        _probs = paddle.tile(self._probs, repeat_times=\
                    [n_samples, *len(self._probs.shape)*[1]])
        sample_ = paddle.bernoulli(_probs)
        self.sample_cache = sample_
        return sample_

    def _log_prob(self, sample=None):

        if sample is None:
            sample = self.sample_cache

        ## Log Prob
        #logits = paddle.log(self._probs /(1-self._probs))
        #log_prob_sample = -fluid.layers.sigmoid_cross_entropy_with_logits(label=sample, x=logits) # check mark

        if len(sample.shape) > len(self._probs.shape):
            _probs = paddle.tile(self._probs, repeat_times=\
                        [sample.shape[0], *len(self._probs.shape)*[1]])
        else:
            _probs = self._probs

        ## add 1e-8 for numerical stable
        log_prob_sample = sample * paddle.log(_probs + 1e-8) \
                            + (1 - sample) * paddle.log(1 - _probs + 1e-8)
        log_prob = fluid.layers.reduce_sum(log_prob_sample, dim=-1)

        return log_prob



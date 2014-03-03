from __future__ import division


class Test:

  def __init__(self):
    from scitbx.array_family import flex

    # Create an image
    self.image = flex.random_double(2000 * 2000)
    self.image.reshape(flex.grid(2000, 2000))
    self.mask = flex.random_bool(2000 * 2000, 0.99)
    self.mask.reshape(flex.grid(2000, 2000))
    self.gain = flex.random_double(2000 * 2000) + 0.5
    self.gain.reshape(flex.grid(2000, 2000))
    self.size = (3, 3)
    self.min_count = 2

  def run(self):
    self.tst_niblack()
    self.tst_sauvola()
    self.tst_fano()
    self.tst_fano_masked()
    self.tst_gain()
    self.tst_kabsch()
    self.tst_kabsch_w_gain()

  def tst_niblack(self):
    from dials.algorithms.image.threshold import niblack
    n_sigma = 3
    result = niblack(self.image, self.size, n_sigma)
    print 'OK'

  def tst_sauvola(self):
    from dials.algorithms.image.threshold import sauvola
    k = 3
    r = 3
    result = sauvola(self.image, self.size, k, r)
    print 'OK'

  def tst_fano(self):
    from dials.algorithms.image.threshold import fano
    n_sigma = 3
    result = fano(self.image, self.size, n_sigma)
    print 'OK'

  def tst_fano_masked(self):
    from dials.algorithms.image.threshold import fano_masked
    n_sigma = 3
    result = fano_masked(self.image, self.mask, self.size, self.min_count, n_sigma)
    print 'OK'

  def tst_gain(self):
    from dials.algorithms.image.threshold import gain
    n_sigma = 3
    result = gain(self.image, self.mask, self.gain, self.size, self.min_count, n_sigma)
    print 'OK'

  def tst_kabsch(self):
    from dials.algorithms.image.threshold import kabsch
    nsig_b = 3
    nsig_s = 3
    result = kabsch(self.image, self.mask, self.size, nsig_b, nsig_s, self.min_count)
    print 'OK'

  def tst_kabsch_w_gain(self):
    from dials.algorithms.image.threshold import kabsch_w_gain
    nsig_b = 3
    nsig_s = 3
    result = kabsch_w_gain(self.image, self.mask, self.gain, self.size, nsig_b, nsig_s, self.min_count)
    print 'OK'

if __name__ == '__main__':
  from dials.test import cd_auto
  with cd_auto(__file__):
    test = Test()
    test.run()

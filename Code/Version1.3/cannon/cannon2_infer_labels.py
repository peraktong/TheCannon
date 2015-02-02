"""This runs Step 2 of The Cannon:
    uses the model to solve for the labels of the test set."""

from __future__ import (absolute_import, division, print_function, unicode_literals)

from scipy import optimize as opt
import numpy as np

def get_lvec(labels):
    """
    Constructs a label vector for an arbitrary number of labels
    Assumes that our model is quadratic in the labels
    """
    nlabels = len(labels)
    lvec = labels # linear terms 
    # Quadratic terms: 
    for i in range(nlabels):
        for j in range(i, nlabels):
            element = labels[i]*labels[j]
            lvec.append(element)
    lvec = np.array(lvec)
    return lvec

def func(coeffs, *labels):
    lvec = get_lvec(list(labels))
    return np.dot(coeffs, lvec)

def infer_labels(model, test_set):
    """
    Uses the model to solve for labels of the test set.

    Input:
    -----
    model: coeffs_all, covs, scatters, chis, chisqs, pivots
    test_set: Dataset object (see Dataset.py) corresponding to the test set.

    Returns
    -------
    test_set: updated Dataset object, with the new labels
    covs_all: covariance matrix of the fit
    """
    print("Inferring Labels...")
    coeffs_all, covs, scatters, red_chisqs, pivots, label_vector = model
    nlabels = len(pivots)
    fluxes = test_set.fluxes
    npixels = len(fluxes)
    ivars = test_set.ivars
    nstars = fluxes.shape[0]
    labels_all = np.zeros((nstars, nlabels))
    # Don't understand what this MCM_rotate_all matrix is
    MCM_rotate_all = np.zeros((nstars, coeffs_all.shape[1]-1, 
                               coeffs_all.shape[1]-1.))
    covs_all = np.zeros((nstars, nlabels, nlabels))

    for jj in range(nstars):
        flux = fluxes[jj,:]
        ivar = ivars[jj,:]
        flux_norm = flux - coeffs_all[:,0]*1 # pivot around the leading term
        Cinv = 1. / ((1./ivar) + scatters**2)
        weights = 1 / Cinv**0.5
        coeffs = np.delete(coeffs_all, 0, axis=1) # take pivot into account
        p0 = np.repeat(1, nlabels)
        try: 
            labels, covs = opt.curve_fit(func, coeffs, flux_norm, 
                                         p0=np.repeat(1,nlabels), 
                                         sigma=weights, absolute_sigma = True)
        except TypeError: #old scipy version
            labels, covs = opt.curve_fit(func, coeffs, flux_norm,
                                         p0=np.repeat(1,nlabels), sigma=weights)
            # rescale covariance matrix
            chi = (flux_norm-func(coeffs, *labels)) / weights
            chi2 = (chi**2).sum()
            dof = npixels-nlabels
            factor = (chi2/dof)
            covs /= factor
        labels = labels + pivots
        MCM_rotate = np.dot(coeffs.T, Cinv[:,None] * coeffs)
        labels_all[jj,:] = labels
        MCM_rotate_all[jj,:,:] = MCM_rotate
        covs_all[jj,:,:] = covs

    test_set.set_label_vals(labels_all)
    return test_set, covs_all


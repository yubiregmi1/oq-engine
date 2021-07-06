# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import warnings
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib.gsim.projects.acme_base import (
    get_phi_ss_at_quantile_ACME)
from openquake.hazardlib.imt import SA
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.gsim.yenier_atkinson_2015 import \
        YenierAtkinson2015BSSA
from openquake.hazardlib.gsim.nga_east import (get_phi_s2ss_at_quantile,
                                               get_tau_at_quantile,
                                               get_phi_ss,
                                               TAU_SETUP,
                                               PHI_SETUP,
                                               PHI_S2SS_MODEL,
                                               TAU_EXECUTION)
warnings.filterwarnings("ignore", category=np.RankWarning)
PATH = os.path.join(os.path.dirname(__file__), "..", "nga_east_tables")


def _get_phi(ergodic, PHI_SS, PHI_S2SS, phi_ss_quantile, phi_model, imt, mag):
    """
    Returns the within-event standard deviation (phi)
    """
    phi = get_phi_ss(imt, mag, PHI_SS)
    # check if phi adjustment (2.6.6) is needed
    # -> if phi < 0.4 in middle branch and T is below 0.5 s
    # -> preserve separation between high and low phi values
    if imt.period < 0.5 and phi_ss_quantile == 0.5:
        phi = max(phi, 0.4)

    elif imt.period < 0.5 and phi_ss_quantile != 0.5:
        # compute phi at quantile 0.5 and take the maximum comp to 0.4
        PHI_SS_0p5 = get_phi_ss_at_quantile_ACME(
                                    PHI_SETUP[phi_model], 0.5)
        phi_0p5 = get_phi_ss(imt, mag, PHI_SS_0p5)

        # make adjustment if needed
        phi = 0.4 + phi - phi_0p5 if phi_0p5 < 0.4 else phi

    if ergodic:
        C = PHI_S2SS[imt]
        phi = np.sqrt(phi ** 2. + C["phi_s2ss"] ** 2.)

    return phi


def _get_tau(tau_model, TAU, imt, mag):
    """
    Returns the inter-event standard deviation (tau)
    """
    return TAU_EXECUTION[tau_model](imt, mag, TAU)


def extrapolate_in_PSA(gmpe, sites, rup, dists, imt_high,
                       set_imt, stds_types, imt):
    extrap_mean = []
    t_log10 = np.log10([im for im in set_imt])
    for d in np.arange(0, len(dists.rjb)):
        dist = DistancesContext()
        if hasattr(dists, 'rjb'):
            dist.rjb = np.array([dists.rjb[d]])
        if hasattr(dists, 'rrup'):
            dist.rrup = np.array([dists.rrup[d]])
        means_log10 = []
        for im in set_imt:
            mean_ln, _ = gmpe.get_mean_and_stddevs(
                sites, rup, dist, SA(im), stds_types)
            mean = np.exp(mean_ln[0])
            means_log10.append(np.log10(mean))

        mb = np.polyfit(t_log10, means_log10, 1)
        mean_imt_log10 = mb[0] * np.log10(imt) + mb[1]
        extrap_mean.append(np.log(10**mean_imt_log10))

    return extrap_mean


def get_acc_from_disp(disp, imt):
    """
    Method is only called when imt.period > cappingp
    :param imt:
        The period
    :param disp:
        Displacement
    :returns:
        Acceleration in log space
    """
    acc = np.log(disp * (2 * np.pi / imt)**2)
    return acc


def get_capping_period(cornerp, gmpe, imt):
    """
    Capping period is the smaller of the corner period and the
    max period of coefficents provided by the GMPE
    """
    try:
        coeffs = gmpe.COEFFS.sa_coeffs
        imts = [*coeffs]
        periods = [imt.period for imt in imts]
        if gmpe.__class__.__name__ == 'BindiEtAl2014Rjb':
            highest_period = 2.0
            periods = [p for p in periods if p <= highest_period]
            set_highest = periods[-5:]
        elif gmpe.__class__.__name__ == 'RietbrockEdwards2019Low':
            set_highest = periods[-2:]
        else:
            set_highest = periods
    except AttributeError:
        coeffs = gmpe.COEFFS_TAB2.sa_coeffs
        imts = [*coeffs]
        periods = [imt.period for imt in imts]
        if gmpe.__class__.__name__ == 'BindiEtAl2014Rjb':
            highest_period = 2.0
            periods = [p for p in periods if p <= highest_period]
            set_highest = periods[-5:]
        elif gmpe.__class__.__name__ == 'RietbrockEdwards2019Low':
            set_highest = periods[-2:]
        else:
            set_highest = periods

    return set_highest


def get_corner_period(mag):
    """
    Corner period given as:
    10^(-1.884 - log10(D_sigma)/3 + 0.5*Mw)
    where D_sigma = 80 bars (8 MPa)
    from 2.6.5: cornerp is to be constrained to not go below 1.0
    """
    D_sigma = 80
    cornerp = 10**(-1.884 - np.log10(D_sigma)/3 + 0.5*mag)
    if cornerp < 1.0:
        cornerp = 1.0
    return cornerp


def get_disp_from_acc(acc, imt):
    """
    Method is only called when imt.period > cappingp
   :param acc:
        Acceleration in log space
   :param imt:
        The period
   :returns:
        Displacement
    """
    disp = np.exp(acc) * imt**2 / (2 * np.pi)**2
    return disp


def get_stddevs(ergodic, PHI_SS, PHI_S2SS, phi_ss_quantile, phi_model,
                tau_model, TAU, mag, imt, stddev_types, num_sites):
    """
    Returns the standard deviations for either the ergodic or
    non-ergodic models
    """
    tau = _get_tau(tau_model, TAU, imt, mag)
    phi = _get_phi(ergodic, PHI_SS, PHI_S2SS, phi_ss_quantile, phi_model,
                   imt, mag)
    sigma = np.sqrt(tau ** 2. + phi ** 2.)
    stddevs = []
    for stddev_type in stddev_types:
        if stddev_type == const.StdDev.TOTAL:
            stddevs.append(sigma + np.zeros(num_sites))
        elif stddev_type == const.StdDev.INTRA_EVENT:
            stddevs.append(phi + np.zeros(num_sites))
        elif stddev_type == const.StdDev.INTER_EVENT:
            stddevs.append(tau + np.zeros(num_sites))
    return stddevs


class YenierAtkinson2015ACME2019(YenierAtkinson2015BSSA):
    """
    This is a modified version of the :class:
    `openquake.hazardlib.gsim.yenier_atkinson_2015.YenierAtkinson2015BSSA`
    which incorporates a correction of the median ground motion based on the
    focal mechanism.

    It also fixes vs30 to 760 m/s
    """
    adapted = True

    def __init__(self):
        # Initialise using the super class
        super().__init__(focal_depth=10., region='CENA')
        # Adjust the set of required parameters for the description of the
        # rupture by adding rake
        _previous = list(super().REQUIRES_RUPTURE_PARAMETERS)
        self.REQUIRES_RUPTURE_PARAMETERS = frozenset(_previous + ['rake'])


def _setup_standard_deviations(gsim):
    # setup tau
    gsim.TAU = get_tau_at_quantile(TAU_SETUP[gsim.tau_model]["MEAN"],
                                   TAU_SETUP[gsim.tau_model]["STD"],
                                   gsim.tau_quantile)
    # setup phi
    PHI_SETUP['global_linear'] = gsim.COEFFS_PHI_SS_GLOBAL_LINEAR
    gsim.PHI_SS = get_phi_ss_at_quantile_ACME(PHI_SETUP[gsim.phi_model],
                                              gsim.phi_ss_quantile)
    # if required setup phis2ss
    if gsim.ergodic:
        if gsim.phi_s2ss_model == 'cena':
            gsim.PHI_S2SS = get_phi_s2ss_at_quantile(
                PHI_S2SS_MODEL[gsim.phi_s2ss_model],
                gsim.phi_s2ss_quantile)
        elif gsim.phi_s2ss_model == 'brb':
            gsim.PHI_S2SS = gsim.COEFFS_PHI_S2SS_BRB
        else:
            opts = "'cena', 'brb', or 'None'"
            raise ValueError('phi_s2ss_model can be {}'.format(opts))


class AlAtikSigmaModel(GMPE):
    """
    Implements a modifiable GMPE that uses the ground-motion standard
    deviation model proposed by Al-Atik in 2015 as described in:

    Al-Atik, L. (2015). "NGA-East: Ground-Motion Standard Deviation Models
    for Central and Eastern North America". PEER Report No. 2015/07, 217
    pages.

    The implementation of the sigma model is the one already available
    in the current implementation of the NGA East GMMs.

    :param GMPE:
        GMPE is the **kwargs describing the GMPE (its name) and the sigma
        and kappa modifications to be imposed
    :param gmpe_name:
        GMPE class that will be adjusted by AlAtikSigmaModel
    :param tau_model:
        Choice of model for the inter-event standard deviation (tau), selecting
        from "global" {default}, "cena" or "cena_constant". default is global
    :param tau_quantile:
        tau quantile used in sigma model. default of None uses the mean.
    :param phi_model:
        Choice of model for the single-station intra-event standard deviation
        (phi_ss), selecting from "global" {default}, "cena" or "cena_constant"
        default is global.
    :param phi_quantile:
        phi quantile used in sigma model. default of None uses the mean.
    :param phi_s2ss_model:
        Choice of station-term s2ss model. Can be either "cena" or None. When
        None is input then the non-ergodic model is used
    :param phi_s2ss_quantile:
        s2ss quantile used in sigma model. default of None uses the mean.
    :param kappa_file:
        tab-delimited file of kappa values per IMT, where first column is
        IMT. includes a header.
    :param kappa_val:
        kappa value corresponding to a column header in kappa_file
    """
    adapted = True

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tau_model = kwargs.get('tau_model', 'global')
        self.phi_model = kwargs.get('phi_model', 'global')
        self.phi_s2ss_model = kwargs.get('phi_s2ss_model')
        self.TAU = None
        self.PHI_SS = None
        self.PHI_S2SS = None
        if self.phi_s2ss_model:
            self.ergodic = True
        else:
            self.ergodic = False
        self.tau_quantile = kwargs.get('tau_quantile')
        self.phi_ss_quantile = kwargs.get('phi_ss_quantile')
        self.phi_s2ss_quantile = kwargs.get('phi_s2ss_quantile')
        _setup_standard_deviations(self)
        self.kappa_file = kwargs.get('kappa_file')
        self.kappa_val = kwargs.get('kappa_val')

        self.gmpe_name = kwargs['gmpe_name']
        self.gmpe = registry[self.gmpe_name]()
        self.set_parameters()

        if self.kappa_file:
            with open(self.kappa_file, r'rb') as myfile:
                data = myfile.read().decode('utf-8')
            self.KAPPATAB = CoeffsTable(table=data, sa_damping=5)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types,
                             extr=True):

        nsites = len(sites)
        stddevs = get_stddevs(
            self.ergodic, self.PHI_SS, self.PHI_S2SS, self.phi_ss_quantile,
            self.phi_model, self.tau_model, self.TAU, rup.mag, imt,
            stds_types, nsites)
        cornerp = get_corner_period(rup.mag)
        # capping period only compares
        # - highest period with a coefficient
        # - corner period
        # - 2.0 if it's bindi
        sp = get_capping_period(cornerp, self.gmpe, imt)
        hp = sp[-1]

        # 1 - if imt.period < cornerp, no changes needed
        if extr and imt.period <= cornerp and imt.period <= hp:
            mean, _ = self.gmpe.get_mean_and_stddevs(
                sites, rup, dists, imt, stds_types)
        # if the period is larger than the corner period but the corner period
        # is less than the highest period
        elif extr and imt.period >= cornerp and cornerp <= hp:
            mean, _ = self.gmpe.get_mean_and_stddevs(
                sites, rup, dists, SA(cornerp), stds_types)
            disp = get_disp_from_acc(mean, cornerp)
            mean = get_acc_from_disp(disp, imt.period)
        # if the corner period is longer than highest and imt is above
        # highets but below corner
        elif extr and cornerp > hp and hp <= imt.period < cornerp:
            mean = extrapolate_in_PSA(
                self.gmpe, sites, rup, dists, hp, sp, stds_types, imt.period)
        elif extr and cornerp > hp and imt.period > cornerp:
            mean = extrapolate_in_PSA(
                self.gmpe, sites, rup, dists, hp, sp, stds_types, cornerp)
            disp = get_disp_from_acc(mean, cornerp)
            mean = get_acc_from_disp(disp, imt.period)

        else:
            mean, _ = self.gmpe.get_mean_and_stddevs(
                sites, rup, dists, imt, stds_types)

        kappa = 1
        if self.kappa_file:

            if imt.period == 0:
                kappa = self.KAPPATAB[SA(0.01)][self.kappa_val]
            elif imt.period > 2.0:
                kappa = self.KAPPATAB[SA(2.0)][self.kappa_val]
            else:
                kappa = self.KAPPATAB[imt][self.kappa_val]

        return mean + np.log(kappa), stddevs

    # PHI_SS2S coefficients, table 2.2 HID
    COEFFS_PHI_S2SS_BRB = CoeffsTable(logratio=False, sa_damping=5., table="""\
        imt   phi_s2ss
        PGA     0.0000
        0.001   0.0000
        0.999   0.0000
        1.000   0.0011
        1.200   0.0040
        1.500   0.0075
        2.000   0.0111
        10.00   0.0111
        """)

    # Phi_ss coefficients for the global model
    COEFFS_PHI_SS_GLOBAL_LINEAR = CoeffsTable(logratio=False, sa_damping=5., table="""\
    imt     mean_a   var_a  mean_b  var_bs
    pgv     0.5034  0.0609  0.3585  0.0316
    pga     0.5477  0.0731  0.3505  0.0412
    0.010   0.5477  0.0731  0.3505  0.0412
    0.020   0.5464  0.0727  0.3505  0.0416
    0.030   0.5450  0.0723  0.3505  0.0419
    0.040   0.5436  0.0720  0.3505  0.0422
    0.050   0.5424  0.0716  0.3505  0.0425
    0.075   0.5392  0.0707  0.3505  0.0432
    0.100   0.5361  0.0699  0.3505  0.0439
    0.150   0.5299  0.0682  0.3543  0.0453
    0.200   0.5240  0.0666  0.3659  0.0465
    0.250   0.5183  0.0651  0.3765  0.0476
    0.300   0.5127  0.0637  0.3876  0.0486
    0.400   0.5022  0.0611  0.4066  0.0503
    0.500   0.4923  0.0586  0.4170  0.0515
    0.750   0.4704  0.0535  0.4277  0.0526
    1.000   0.4519  0.0495  0.4257  0.0508
    1.500   0.4231  0.0439  0.4142  0.0433
    2.000   0.4026  0.0405  0.4026  0.0396
    3.000   0.3775  0.0371  0.3775  0.0366
    4.000   0.3648  0.0358  0.3648  0.0358
    5.000   0.3583  0.0353  0.3583  0.0356
    7.500   0.3529  0.0350  0.3529  0.0355
    10.00   0.3519  0.0350  0.3519  0.0355
    """)

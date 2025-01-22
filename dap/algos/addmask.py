#TODO: find a better way to handle this

def calc_apply_additional_mask(results, pixel_mask_pf):
    apply_additional_mask = results.get("apply_additional_mask", False)
    if not apply_additional_mask:
        return

    detector_name = results.get("detector_name", None)
    if not detector_name:
        return

    if detector_name == "JF06T08V07":
        # edge pixels
        pixel_mask_pf[0:1030, 1100] = 0
        pixel_mask_pf[0:1030, 1613] = 0
        pixel_mask_pf[0:1030, 1650] = 0

        pixel_mask_pf[67, 0:1063] = 0

        pixel_mask_pf[67:1097, 513] = 0
        pixel_mask_pf[67:1097, 550] = 0
        pixel_mask_pf[67:1097, 1063] = 0

        pixel_mask_pf[1029, 1100:1614] = 0
        pixel_mask_pf[1029, 1650:2163] = 0

        pixel_mask_pf[1039, 1168:1682] = 0
        pixel_mask_pf[1039, 1718:2230] = 0

        pixel_mask_pf[1039:2069, 1168] = 0
        pixel_mask_pf[1039:2069, 1681] = 0
        pixel_mask_pf[1039:2069, 1718] = 0

        pixel_mask_pf[1096, 0:513] = 0
        pixel_mask_pf[1096, 550:1064] = 0

        pixel_mask_pf[1106, 68:582] = 0
        pixel_mask_pf[1106, 618:1132] = 0

        pixel_mask_pf[1106:2136, 581] = 0
        pixel_mask_pf[1106:2136, 618] = 0
        pixel_mask_pf[1106:2136, 1131] = 0

        pixel_mask_pf[2068, 1168:2232] = 0

        # first bad region in left bottom inner module
        pixel_mask_pf[842:1097, 669:671] = 0

        # second bad region in left bottom inner module
        pixel_mask_pf[1094, 620:807] = 0

        # vertical line in upper left bottom module
        pixel_mask_pf[842:1072, 87:90] = 0

        # horizontal line?
        pixel_mask_pf[1794, 1503:1550] = 0


    elif detector_name == "JF17T16V01":
        # mask module 11
        pixel_mask_pf[2619:3333,1577:2607] = 0




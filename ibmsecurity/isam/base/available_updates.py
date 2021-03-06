import logging

logger = logging.getLogger(__name__)


def get(isamAppliance, check_mode=False, force=False):
    """
    Retrieve available updates
    """
    return isamAppliance.invoke_get("Retrieving available updates",
                                    "/updates/available.json")


def discover(isamAppliance, check_mode=False, force=False):
    """
    Discover available updates
    """
    return isamAppliance.invoke_get("Discover available updates",
                                    "/updates/available/discover")


def upload(isamAppliance, file, check_mode=False, force=False):
    """
    Upload Available Update
    """
    if force is True or _check_file(isamAppliance, file) is False:
        if check_mode is True:
            return isamAppliance.create_return_object(changed=True)
        else:
            return isamAppliance.invoke_post_files(
                "Upload Available Update",
                "/core/updates/available",
                [{
                    'file_formfield': 'uploadedfile',
                    'filename': file,
                    'mimetype': 'application/octet-stream'
                }],
                {})

    return isamAppliance.create_return_object()


def _check_file(isamAppliance, file):
    """
    Parse the file name to see if it is already uploaded - use version and release date from pkg file name
    Also check to see if the firmware level is already uploaded
    Note: Lot depends on the name of the file.

    :param isamAppliance:
    :param file:
    :return:
    """
    import os.path

    # If there is an exception then simply return False
    # Sample filename - isam_9.0.2.0_20161102-2353.pkg
    logger.debug("Checking provided file is ready to upload: {0}".format(file))
    try:
        # Extract file name from path
        f = os.path.basename(file)
        fn = os.path.splitext(f)
        logger.debug("File name without path: {0}".format(fn[0]))

        # Discard everything after the "-" hyphen
        fp, d = f.split('-')
        logger.debug("File name without extension: {0}".format(fp))
        # Split the remainder of file by '_' under score
        fp = fp.split('_')
        logger.debug("{0}: version: {1} date: {2}".format(fp[0], fp[1], fp[2]))

        # Check if firmware level already contains the update to be uploaded or greater, check Active partition
        # firmware "name" of format - isam_9.0.2.0_20161102-2353
        import ibmsecurity.isam.base.firmware
        ret_obj = ibmsecurity.isam.base.firmware.get(isamAppliance)
        for firm in ret_obj['data']:
            if firm['active'] is True and firm['name'] >= fn[0]:
                logger.info(
                    "Active partition has version {0} which is greater or equals install package at version {1}.".format(
                        firm['name'], fn[0]))
                return True

        # Check if update uploaded - will not show up if installed though
        ret_obj = get(isamAppliance)
        for upd in ret_obj['data']:
            rd = upd['release_date']
            rd = rd.replace('-', '')  # turn release date into 20161102 format from 2016-11-02
            if upd['version'] == fp[1] and rd == fp[2]:  # Version of format 9.0.2.0
                return True
    except:
        pass

    return False


def install(isamAppliance, type, version, release_date, name, check_mode=False, force=False):
    """
    Install Available Update
    """
    if force is True or _check(isamAppliance, type, version, release_date, name) is True:
        if check_mode is True:
            return isamAppliance.create_return_object(changed=True)
        else:
            ret_obj = isamAppliance.invoke_post("Install Available Update",
                                                "/updates/available/install",
                                                {"updates": [
                                                    {
                                                        "type": type,
                                                        "version": version,
                                                        "release_date": release_date,
                                                        "name": name
                                                    }
                                                ]
                                                })
            isamAppliance.facts['version'] = version
            return ret_obj

    return isamAppliance.create_return_object()


def _check(isamAppliance, type, version, release_date, name):
    ret_obj = get(isamAppliance)
    for upd in ret_obj['data']:
        # If there is an installation in progress then abort
        if upd['state'] == 'Installing':
            logger.debug("Detecting a state of installing...")
            return False
        if upd['type'] == type and upd['version'] == version and upd['release_date'] == release_date and upd[
            'name'] == name:
            logger.debug("Requested firmware ready for install...")
            return True

    logger.debug("Requested firmware not available for install...")

    return False

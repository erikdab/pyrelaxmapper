# -*- coding: utf-8 -*-
import logging
import os
import pickle
import shutil
import time

from pyrelaxmapper.fileutils import ensure_dir, ensure_ext, ensure_path

logger = logging.getLogger()


# TODO: Better extension handling
# TODO: Default name is type name
class DirManager:
    """Directory Manager, simplifying many common tasks.

    Performs all its operations inside of its "managed directory".

    Parameters
    ----------
    directory : str
        Directory in which all files are saved/ loaded, etc.
    main_group : str
        Main group.
    """

    def __init__(self, directory, main_group='', extension='.pkl'):
        self._directory = ensure_dir(os.path.expanduser(directory))
        self._main_group = main_group
        self._extension = extension

    def __str__(self):
        return '{}(dir:"{}")'.format(type(self).__name__, self._directory)

    def r(self, name, main_group=False, group=None):
        """Load file inside managed directory.

        Parameters
        ----------
        name : str
            Name
        main_group : bool
            If should use main context group.
        group : str
            File group (folder)
            If main_group is set, will be placed inside it.
        """
        path = ensure_ext(self.path(name, main_group, group), self._extension)
        try:
            return self._load_obj(path)
        except FileNotFoundError as e:
            logger.debug('Reading error "{}". File: {}.'.format(e, path))

    def w(self, name, obj, main_group=False, group=None):
        """Load file inside managed directory.

        Parameters
        ----------
        name : str
            Name
        obj : any
            Object to save if file does not exist.
        main_group : bool
            If should use main context group.
        group : str
            File group (folder)
            If main_group is set, will be placed inside it.
        """
        path = ensure_ext(self.path(name, main_group, group), self._extension)
        try:
            self._save_obj(obj, path)
        except FileNotFoundError as e:
            logger.debug('Writing error "{}". File: {}.'.format(e, path))

    def rw(self, name, obj, main_group=False, group=None, force=False):
        """Load or write object instance inside managed directory.

        Parameters
        ----------
        name : str
            Name
        obj : any
            Object to save if file does not exist.
        main_group : bool
            If should use main context group.
        group : str
            File group (folder)
            If main_group is set, will be placed inside it.
        force : bool
            Force overwrite.
        """
        return self.rw_lazy(name, lambda: obj, [], main_group, group, force)

    def rw_lazy(self, name, call, args=None, main_group=False, group=None, force=False):
        """Load or write callable inside managed directory.

        Parameters
        ----------
        name : str
            Name
        call
            Any callable: lambda, function, class, etc.
            Its result is saved to file if file does not exist.
        args : optional
            Args to pass to callable.
        main_group : bool
            If should use main context group.
        group : str
            File group (folder)
            If main_group is set, will be placed inside it.
        force : bool
            Force overwrite.
        """
        if args is None:
            args = []
        elif not isinstance(args, list):
            args = [args]

        path = ensure_ext(self.path(name, main_group, group), self._extension)
        exists = os.path.exists(path)
        source = 'from cache' if exists else 'live'
        group_name = '{}/{}'.format(group, name) if group else name

        logger.info('Loading "{}" {}.'.format(group_name, source))

        data = None
        tic = time.clock()
        if exists and not force:
            try:
                data = self._load_obj(path)
            except FileNotFoundError as e:
                logger.debug('Reading error "{}". File: {}.'.format(e, path))
        if not data:
            data = call(*args)
            self._save_obj(data, path)
        tic = time.clock() - tic

        logger.info('Loaded "{}" in {:.4f} sec.'.format(group_name, tic))
        return data

    def remove(self, name, main_group=False, group=None):
        """Remove file in managed directory.

        Parameters
        ----------
        name : str
            Name
        main_group : bool
            If should use main context group.
        group : str
            File group (folder)
            If main_group is set, will be placed inside it.
        """
        name = ensure_ext(name, self._extension)
        path = self.path(name, main_group, group)
        if os.path.exists(self.path(name, main_group, group)):
            os.remove(path)

    def exists(self, name, main_group=False, group=None):
        """Check file existence in managed directory.

        Parameters
        ----------
        name : str
            Name
        main_group : bool
            If should use main context group.
        group : str
            File group (folder)
            If main_group is set, will be placed inside it.
        """
        name = ensure_ext(name, self._extension)
        return os.path.exists(self.path(name, main_group, group))

    def remove_all(self):
        """Recursively Remove ALL files in managed directory."""
        shutil.rmtree(self._directory)
        os.makedirs(self._directory)

    # Extension
    def path(self, filename='', main_group=False, group=None, ensure=True):
        """Path to file inside managed directory."""
        directory = self._directory
        if main_group:
            directory = os.path.join(directory, self._main_group)
        if group is not None:
            directory = os.path.join(directory, group)

        if ensure:
            return ensure_path(directory, filename)
        else:
            return os.path.join(directory, filename)

    def dir(self, main_group=False, group=None):
        return self.path('', main_group, group)

    @staticmethod
    def _save_obj(obj, filename):
        """Pickle object to filename.

        Parameters
        ----------
        obj : any
        filename : str
        """
        with open(filename, 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _load_obj(filename):
        """Loads pickled object from filename.

        Parameters
        ----------
        filename : str
        """
        with open(filename, 'rb') as f:
            return pickle.load(f)

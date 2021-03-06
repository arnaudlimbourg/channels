from __future__ import unicode_literals

from django.core.management import BaseCommand, CommandError
from channels import channel_layers, DEFAULT_CHANNEL_LAYER
from channels.log import setup_logger
from channels.worker import Worker


class Command(BaseCommand):

    leave_locale_alone = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--layer', action='store', dest='layer', default=DEFAULT_CHANNEL_LAYER,
            help='Channel layer alias to use, if not the default.')

    def handle(self, *args, **options):
        # Get the backend to use
        self.verbosity = options.get("verbosity", 1)
        self.logger = setup_logger('django.channels', self.verbosity)
        self.channel_layer = channel_layers[options.get("layer", DEFAULT_CHANNEL_LAYER)]
        # Check that handler isn't inmemory
        if self.channel_layer.local_only():
            raise CommandError(
                "You cannot span multiple processes with the in-memory layer. " +
                "Change your settings to use a cross-process channel layer."
            )
        # Check a handler is registered for http reqs
        self.channel_layer.router.check_default()
        # Launch a worker
        self.logger.info("Running worker against channel layer %s", self.channel_layer)
        # Optionally provide an output callback
        callback = None
        if self.verbosity > 1:
            callback = self.consumer_called
        # Run the worker
        try:
            Worker(channel_layer=self.channel_layer, callback=callback).run()
        except KeyboardInterrupt:
            pass

    def consumer_called(self, channel, message):
        self.logger.debug("%s", channel)

# LIBTBX_SET_DISPATCHER_NAME dev.dials.show_extensions


import dials.util


class Script:
    """The class to encapsulate the script."""

    def __init__(self):
        """Initialise the script."""
        from libtbx.phil import parse

        from dials.util.options import OptionParser

        # Create the phil parameters
        phil_scope = parse(
            """
      interfaces=False
        .type = bool
        .help = "Only show information about the interfaces"
    """
        )

        # Create the option parser
        usage = "dev.dials.show_extensions [options] /path/to/image/files"
        self.parser = OptionParser(usage=usage, phil=phil_scope)

    def run(self, args=None):
        """Run the script."""
        import dials.extensions

        # Parse the command line arguments
        params, options = self.parser.parse_args(args)

        # Create the list of interfaces
        interfaces = [
            dials.extensions.ProfileModel,
            dials.extensions.Background,
            dials.extensions.Centroid,
            dials.extensions.SpotFinderThreshold,
        ]

        # Loop through all the interfaces
        for iface in interfaces:
            print("-" * 80)
            print("Extension interface: %s" % iface.__name__)

            # Either just show information about interfaces or show some about
            # extensions depending on user input
            if params.interfaces:

                # Print info about interface
                if options.verbose > 0:
                    print(" name = %s" % iface.name)
                    if options.verbose > 1:
                        level = options.verbose - 2
                        scope = iface.phil_scope()
                        phil = scope.as_str(print_width=80 - 3, attributes_level=level)
                        phil = "\n".join((" " * 2) + l for l in phil.split("\n"))
                        if phil.strip() != "":
                            print(" phil:\n%s" % phil)

            else:

                # Loop through all the extensions
                for ext in iface.extensions():
                    print(" Extension: %s" % ext.__name__)
                    if options.verbose > 0:
                        print("  name = %s" % ext.name)
                        if options.verbose > 1:
                            level = options.verbose - 2
                            scope = ext.phil_scope()
                            phil = scope.as_str(
                                print_width=80 - 3, attributes_level=level
                            )
                            phil = "\n".join((" " * 3) + l for l in phil.split("\n"))
                            if phil.strip() != "":
                                print("  phil:\n%s" % phil)


@dials.util.show_mail_handle_errors()
def run(args=None):
    script = Script()
    script.run(args)


if __name__ == "__main__":
    run()

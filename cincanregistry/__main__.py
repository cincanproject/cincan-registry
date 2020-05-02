from . import ToolRegistry
from . import VersionInfo
import argparse
import sys
import logging
import asyncio
import pathlib
from typing import List
import json
import os

# from .checkers._checker import _sort_latest_tag
DEFAULT_IMAGE_FILTER_TAG = "latest-stable"

PRE_SPACE = 0
# Name length
MAX_WN = 35
# Size width
MAX_WS = 10


# Base version length, showing only first 8 chars.
# Hash can be 40 chars long
CHARS_TO_SHOW = 20
# Version Length
MAX_WV = CHARS_TO_SHOW + 1
# Version length with provider
MAX_WVP = MAX_WV + 20
# Tag(s) length
MAX_WT = 20
# Description length
MAX_WD = 30

EXTRA_FILL = 35


class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    GREEN_BACKGROUND = "\033[102m"
    YELLOW = "\033[93m"
    GRAY = "\033[37m"
    GRAY_BACKGROUND = "\033[47m"
    RED = "\033[31m"
    RED_BACKGROUND = "\033[41m"
    BOLD_RED = "\033[1m\033[31m"
    BOLD = "\033[1m"
    BOLD_YELLOW = "\033[1m\033[33m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_single_tool_version_check(tool):
    print(
        f"Name: {tool.get('name')}\nLocal version: {tool.get('versions').get('local')}\nRemote version: {tool.get('versions').get('local')}\nOrigin Version: {tool.get('versions').get('origin')}"
    )
    for other in tool.get("versions").get("other"):
        print(f"{other.get('provider')} version: {other.get('version')}")

    print("\nUse -j flag to print as JSON with additional details.\n")


def print_version_check(tools:dict, location="both", only_updates:bool=False):

    print(f"\n{' ':<{PRE_SPACE}}Color explanations:", end=" ")
    print(f"{color.GREEN_BACKGROUND}  {color.END} - tool up to date", end=" ")
    print(f"{color.RED_BACKGROUND}  {color.END} - update available in remote", end=" ")
    print(f"{color.GRAY_BACKGROUND}  {color.END} - remote differs from tool origin")

    print(
        f"\n{' ':<{PRE_SPACE}}By default, only versions for available local tools are visible."
    )
    print(
        f"\n{' ':<{PRE_SPACE}}Only first {CHARS_TO_SHOW} characters are showed from version."
    )
    print(
        f"\n{' ':<{PRE_SPACE}}(*) means, that origin provider is Dockerfile installation origin, not tool origin."
    )

    # pre-space and text format
    print(f"\n{' ':<{PRE_SPACE}}{color.BOLD}  ", end="")
    # name
    print(f"{'Tool name':<{MAX_WN}}", end="")
    # local ver
    print(f"{f'Local Version':{MAX_WV}}", end="")
    # registry ver
    print(f"{f'DockerHub Version':{MAX_WV}}", end="")
    # origin ver
    print(f"{f'Origin Version':{MAX_WV}}", end="")
    # origin provider
    print(f"{f'Origin Provider':{MAX_WVP}}", end="")
    # end text format
    print(f"{color.END}\n")

    for tool_name in sorted(tools):

        coloring = color.GREEN

        tool = tools[tool_name]


        if tool.get("updates").get("local") and location in ["local", "both"]:
            coloring = color.BOLD_RED
        elif tool.get("updates").get("remote"):
            coloring = color.GRAY
        if location == "local":
            if not tool.get("versions").get("local").get("version"):
                continue
        if location == "remote" and only_updates:
            if not tool.get("updates").get("remote"):
                continue           

        # pre-space and color
        print(f"{coloring}{' ':<{PRE_SPACE}}| ", end="")
        # name
        print(f"{tool_name:<{MAX_WN}}", end="")
        # local version
        versions = tool.get("versions")
        print(
            f"{versions.get('local').get('version')[:CHARS_TO_SHOW]:{MAX_WV}}", end="",
        )
        # remote version
        print(
            f"{versions.get('remote').get('version')[:CHARS_TO_SHOW]:<{MAX_WV}}",
            end="",
        )

        ### origin check ####
        org_details = versions.get("origin").get("details")
        if (
            org_details
            and not org_details.get("origin")
            and org_details.get("docker_origin")
        ):
            mark_as_not_source = "(*)"
        else:
            mark_as_not_source = ""

        # origin version
        print(
            f"{versions.get('origin').get('version')[:CHARS_TO_SHOW]:<{MAX_WV}}",
            end="",
        )
        # origin provider
        print(
            f"{(org_details.get('provider') + mark_as_not_source) if org_details else '':<{MAX_WVP}}",
            end="",
        )
        # end colored section
        print(f"{color.END if coloring else None}")


def print_tools_by_location(
    tools: List[dict], location: str, filter_by: str = "", show_size=False
):

    MAX_WV = 41
    if location == "remote" and show_size:
        print(f"{' ':<{PRE_SPACE}} Size as compressed in Remote.")
    if location == "local" and show_size:
        print(f"{' ':<{PRE_SPACE}} Size as uncompressed in Local.")
    print(f"\n{' ':<{PRE_SPACE}}{color.BOLD}  ", end="")
    print(f"{'Tool name':<{MAX_WN}}  ", end="")
    print(f"{f'{location.capitalize()} Version':{MAX_WV}}  ", end="")
    if show_size:
        print(f"{'Size':<{MAX_WS}}   ", end="")
    print(f"{f'{location.capitalize()} Tags':<{MAX_WT}}", end="")
    print(f"{color.END}\n")
    if not filter_by:
        print(f"{' ':<{PRE_SPACE}}{'':-<{MAX_WN + MAX_WT + MAX_WV + EXTRA_FILL}}")
    for tool in sorted(tools):
        lst = tools[tool]
        first_print = True
        if lst.versions and len(lst.versions) == 1:
            tags = ",".join(next(iter(lst.versions)).tags)
            size = next(iter(lst.versions)).size
            version = next(iter(lst.versions)).version
            name = lst.name.split(":")[0]
            if filter_by and filter_by not in tags:
                continue
            print(f"{' ':<{PRE_SPACE}}| ", end="")
            print(f"{name:<{MAX_WN}}| ", end="")
            print(f"{version:{MAX_WV}}| ", end="")
            if show_size:
                print(f"{size:>{MAX_WS}} | ", end="")
            print(f"{tags:<{MAX_WT}}")
            first_print = False
        else:
            tags = ""
            version = ""
            for i, ver in enumerate(lst.versions):
                name = lst.name.split(":")[0] if first_print else ""
                tags = ",".join(lst.versions[i].tags)
                version = ver.version
                size = ver.size
                if filter_by and filter_by not in tags:
                    continue
                print(f"{' ':<{PRE_SPACE}}| ", end="")
                print(f"{name:<{MAX_WN}}| ", end="")
                print(f"{version:{MAX_WV}}| ", end="")
                if show_size:
                    print(f"{size:>{MAX_WS}} | ", end="")
                print(f"{tags:<{MAX_WT}}")
                first_print = False

        if lst.versions and not first_print and not filter_by:
            print(f"{' ':<{PRE_SPACE}}{'':-<{MAX_WN + MAX_WT + MAX_WV + EXTRA_FILL}}")


def print_combined_local_remote(tools: dict, show_size=False):

    print(f"\n{' ':<{PRE_SPACE}}{color.BOLD} ", end="")
    print(f"{'Tool name':<{MAX_WN}}", end="")
    print(f"{f'Local Version':{MAX_WV}}", end="")
    print(f"{'Remote Version':<{MAX_WV}}", end="")
    if show_size:
        print(f" {'R. Size':<{MAX_WS}}", end="")
    print(f"{f'Description':<{MAX_WD}}", end="")
    print(f"{color.END}\n")

    for tool in sorted(tools):
        l_version = tools[tool].get("local_version")[:CHARS_TO_SHOW]
        r_version = tools[tool].get("remote_version")[:CHARS_TO_SHOW]
        description = tools[tool].get("description")

        print(f"{' ':<{PRE_SPACE}}|", end="")
        print(f"{tool:<{MAX_WN}}", end="")
        print(f"{l_version:{MAX_WV}}", end="")
        print(f"{r_version:{MAX_WV}}", end="")
        if show_size:
            size = tools[tool].get("compressed_size")
            print(f"{size:>{MAX_WS}} ", end="")
        print(f"{description:<{MAX_WD}}")


def main():

    m_parser = argparse.ArgumentParser()
    m_parser.add_argument(
        "-l",
        "--log",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
        default=None,
    )
    m_parser.add_argument("-q", "--quiet", action="store_true", help="Be quite quiet")
    subparsers = m_parser.add_subparsers(dest="sub_command")

    list_parser = subparsers.add_parser(
        "list", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    list_exclusive_group = list_parser.add_mutually_exclusive_group()
    list_exclusive_group.add_argument(
        "-t",
        "--tag",
        default=DEFAULT_IMAGE_FILTER_TAG,
        help="Filter images by tag name.",
    )
    list_exclusive_group.add_argument(
        "-a", "--all", action="store_true", help="List all images from the registry."
    )
    list_parser.add_argument(
        "-s",
        "--size",
        action="store_true",
        help="Include size in listing. Compressed on remote, uncompressed on local.",
    )
    list_parser.add_argument(
        "-j", "--json", action="store_true", help="Print output in JSON format."
    )
    list_second_exclusive = list_parser.add_mutually_exclusive_group()
    list_second_exclusive.add_argument(
        "-r",
        "--remote",
        action="store_true",
        help="List remote 'cincan' tools from registry.",
    )
    list_second_exclusive.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="List only locally available 'cincan' tools.",
    )
    subsubparsers = list_parser.add_subparsers(dest="list_sub_command")
    version_parser = subsubparsers.add_parser(
        "versions",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="List all versions of the tools.",
    )
    version_parser.add_argument(
        "-n", "--name", help="Check single tool by the name.",
    )
    version_parser.add_argument(
        "-u", "--only-updates", action="store_true", help="Lists only available updates.",
    )
    version_parser.add_argument(
        "--metadir-path",
        help="Override default path for available meta files. (Directory) This directory should contain upstream information for each tool.",
    )
    if len(sys.argv) > 1:
        args = m_parser.parse_args(args=sys.argv[1:])
    else:
        args = m_parser.parse_args(args=["help"])

    sub_command = args.sub_command

    log_level = (
        args.log_level if args.log_level else ("WARNING" if args.quiet else "INFO")
    )
    if log_level not in {"DEBUG"}:
        sys.tracebacklimit = 0  # avoid track traces unless debugging
    logging.basicConfig(
        format=f"{' ':<{PRE_SPACE}}%(levelname)s - %(name)s: %(message)s",
        level=getattr(logging, log_level),
    )

    if sub_command == "help":
        m_parser.print_help()
        sys.exit(1)

    elif sub_command == "list":

        reg = ToolRegistry()

        if not args.list_sub_command:

            if args.local or args.remote:

                loop = asyncio.get_event_loop()
                try:
                    if args.local:
                        tools = loop.run_until_complete(
                            reg.list_tools_local_images(
                                defined_tag=args.tag if not args.all else ""
                            )
                        )
                    elif args.remote:
                        tools = loop.run_until_complete(
                            reg.list_tools_registry(
                                defined_tag=args.tag if not args.all else ""
                            )
                        )

                finally:
                    loop.close()
                if tools:
                    if not args.all and not args.json:
                        print(f"\n  Listing all tools with tag '{args.tag}':\n")
                    elif not args.all and args.json:
                        raise NotImplementedError
                        print(json.dumps(tools))
                    else:
                        print(f"\n  Listing all tools :\n")

                    location = "local" if args.local else "remote"

                    print_tools_by_location(
                        tools, location, args.tag if not args.all else "", args.size
                    )

        elif args.list_sub_command == "versions":
            loop = asyncio.get_event_loop()
            ret = loop.run_until_complete(
                reg.list_versions(
                    tool=args.name or "",
                    toJSON=args.json or False,
                    metadir_path=args.metadir_path or "",
                    only_updates=args.only_updates
                )
            )
            # os.system("clear")
            if args.name and not args.json:
                print_single_tool_version_check(ret)
            elif not args.name and not args.json:
                loc = "remote" if args.remote else ("local" if args.local else "both")
                print_version_check(ret, loc, args.only_updates)
            if args.json:
                print(ret)
            loop.close()

        else:

            tool_list = reg.list_tools(defined_tag=args.tag if not args.all else "")
 
            if not args.all and not args.json and tool_list:
                print(f"\n  Listing all tools with tag '{args.tag}':\n")
            if not args.json and tool_list:
                print_combined_local_remote(tool_list, args.size)
            elif tool_list:
                print(json.dumps(tool_list))
            else:
                print("No single tool available for unknown reason.")


if __name__ == "__main__":
    main()

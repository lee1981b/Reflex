"""The route decorator and associated variables and functions."""

from __future__ import annotations

import re

from reflex import constants


def verify_route_validity(route: str) -> None:
    """Verify if the route is valid, and throw an error if not.

    Args:
        route: The route that need to be checked

    Raises:
        ValueError: If the route is invalid.
    """
    pattern = catchall_in_route(route)
    if pattern:
        if pattern != "[[...splat]]":
            msg = f"Catchall pattern `{pattern}` is not valid. Only `[[...splat]]` is allowed."
            raise ValueError(msg)
        if not route.endswith(pattern):
            msg = f"Catchall pattern `{pattern}` must be at the end of the route."
            raise ValueError(msg)


def get_route_args(route: str) -> dict[str, str]:
    """Get the dynamic arguments for the given route.

    Args:
        route: The route to get the arguments for.

    Returns:
        The route arguments.
    """
    args = {}

    def add_route_arg(match: re.Match[str], type_: str):
        """Add arg from regex search result.

        Args:
            match: Result of a regex search
            type_: The assigned type for this arg

        Raises:
            ValueError: If the route is invalid.
        """
        arg_name = match.groups()[0]
        if arg_name in args:
            msg = f"Arg name [{arg_name}] is used more than once in this URL"
            raise ValueError(msg)
        args[arg_name] = type_

    # Regex to check for route args.
    check = constants.RouteRegex.ARG
    check_strict_catchall = constants.RouteRegex.STRICT_CATCHALL
    check_opt_catchall = constants.RouteRegex.OPT_CATCHALL

    # Iterate over the route parts and check for route args.
    for part in route.split("/"):
        match_opt = check_opt_catchall.match(part)
        if match_opt:
            add_route_arg(match_opt, constants.RouteArgType.LIST)
            break

        match_strict = check_strict_catchall.match(part)
        if match_strict:
            add_route_arg(match_strict, constants.RouteArgType.LIST)
            break

        match = check.match(part)
        if match:
            # Add the route arg to the list.
            add_route_arg(match, constants.RouteArgType.SINGLE)
    return args


def catchall_in_route(route: str) -> str:
    """Extract the catchall part from a route.

    Example:
        >>> catchall_in_route("/posts/[...slug]")
        '[...slug]'
        >>> catchall_in_route("/posts/[[...slug]]")
        '[[...slug]]'
        >>> catchall_in_route("/posts/[slug]")
        ''

    Args:
        route: the route from which to extract

    Returns:
        str: the catchall part of the URI
    """
    match_ = constants.RouteRegex.CATCHALL.search(route)
    return match_.group() if match_ else ""


def replace_brackets_with_keywords(input_string: str) -> str:
    """Replace brackets and everything inside it in a string with a keyword.

    Args:
        input_string: String to replace.

    Returns:
        new string containing keywords.
    """
    # /posts -> /post
    # /posts/[slug] -> /posts/__SINGLE_SEGMENT__
    # /posts/[slug]/comments -> /posts/__SINGLE_SEGMENT__/comments
    # /posts/[[slug]] -> /posts/__DOUBLE_SEGMENT__
    # / posts/[[...slug2]]-> /posts/__DOUBLE_CATCHALL_SEGMENT__
    # /posts/[...slug3]-> /posts/__SINGLE_CATCHALL_SEGMENT__

    # Replace [[...<slug>]] with __DOUBLE_CATCHALL_SEGMENT__
    output_string = re.sub(
        r"\[\[\.\.\..+?\]\]",
        constants.RouteRegex.DOUBLE_CATCHALL_SEGMENT,
        input_string,
    )
    # Replace [...<slug>] with __SINGLE_CATCHALL_SEGMENT__
    output_string = re.sub(
        r"\[\.\.\..+?\]",
        constants.RouteRegex.SINGLE_CATCHALL_SEGMENT,
        output_string,
    )
    # Replace [[<slug>]] with __DOUBLE_SEGMENT__
    output_string = re.sub(
        r"\[\[.+?\]\]", constants.RouteRegex.DOUBLE_SEGMENT, output_string
    )
    # Replace [<slug>] with __SINGLE_SEGMENT__
    return re.sub(r"\[.+?\]", constants.RouteRegex.SINGLE_SEGMENT, output_string)

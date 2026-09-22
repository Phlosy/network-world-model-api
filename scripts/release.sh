#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)

usage() {
	cat <<'EOF'
Usage:
  scripts/release.sh set-version X.Y.Z
  scripts/release.sh tag X.Y.Z

set-version updates VERSION and the Python package version metadata.
tag creates local annotated vX.Y.Z and go/vX.Y.Z tags at HEAD.

This script never commits or pushes.
EOF
}

fail() {
	printf 'release: %s\n' "$*" >&2
	exit 1
}

validate_version() {
	case "$1" in
		0 | 0.0 | *[!0-9.]* | .* | *. | *..*)
			fail "version must have the form X.Y.Z"
			;;
	esac

	old_ifs=$IFS
	IFS=.
	set -- $1
	IFS=$old_ifs
	[ "$#" -eq 3 ] || fail "version must have the form X.Y.Z"
	for component in "$@"; do
		case "$component" in
			0 | [1-9] | [1-9][0-9]*) ;;
			*) fail "version components must be decimal integers without leading zeroes" ;;
		esac
	done
}

check_version() {
	expected=$1

	[ "$(sed -n '1p' "$repo_dir/VERSION")" = "$expected" ] ||
		fail "VERSION does not contain $expected"
}

set_version() {
	version=$1
	validate_version "$version"

	printf '%s\n' "$version" >"$repo_dir/VERSION"

	# Update Python __version__
	sed -i -E "s/__version__ = \".*\"/__version__ = \"$version\"/" "$repo_dir/python/network_world_model_api/__init__.py"
	# Update Python pyproject.toml version
	sed -i -E "s/^version = \".*\"/version = \"$version\"/" "$repo_dir/python/pyproject.toml"

	check_version "$version"
	printf 'release: updated version to %s\n' "$version"
}

create_tag() {
	version=$1
	validate_version "$version"
	check_version "$version"

	if ! git -C "$repo_dir" diff --quiet || ! git -C "$repo_dir" diff --cached --quiet; then
		fail "working tree has uncommitted changes"
	fi

	for tag in "v$version" "go/v$version"; do
		if git -C "$repo_dir" rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
			fail "tag $tag already exists"
		fi
	done

	git -C "$repo_dir" tag -a "v$version" -m "network-world-model-api release $version"
	git -C "$repo_dir" tag -a "go/v$version" -m "network-world-model-api Go module release $version"

	printf 'release: created annotated tags v%s and go/v%s at %s\n' \
		"$version" "$version" "$(git -C "$repo_dir" rev-parse --short HEAD)"
}

case "${1:-}" in
	set-version)
		[ "${#}" -eq 2 ] || {
			usage >&2
			exit 1
		}
		set_version "$2"
		;;
	tag)
		[ "${#}" -eq 2 ] || {
			usage >&2
			exit 1
		}
		create_tag "$2"
		;;
	*)
		usage >&2
		exit 1
		;;
esac

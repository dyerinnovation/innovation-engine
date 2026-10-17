#!/usr/bin/env bash
# Scrub gate: fail if any published file carries content that should stay private.
#
# Public checks (generic, safe to publish): absolute home paths, email addresses
# (example.com/org/net and the project contact address allowed), em dashes, and italics markers.
# Private checks: scripts/scrub-patterns.local, one case-insensitive Perl regex per line
# (blank lines and # comments ignored). That file is git-ignored; keep product names,
# hosts and people there. Prefix a line with "except=<path> " to skip files under that path.
#
# Usage: scripts/scrub-gate.sh [root]   (exit 0 = clean, 1 = hits)
set -euo pipefail

root=${1:-$(cd "$(dirname "$0")/.." && pwd)}
local_patterns="$root/scripts/scrub-patterns.local"

files=()
while IFS= read -r -d '' f; do files+=("$f"); done < <(
  find "$root" -type d \( -name .git -o -name node_modules \) -prune -o \
    -type f ! -name 'scrub-patterns.local' ! -name '.DS_Store' -print0 | sort -z)

SCRUB_ROOT="$root" SCRUB_LOCAL="$local_patterns" perl -CSD -e '
use strict; use warnings;
my @pub = (
  ["home-path", qr{(?:/(?:Users|home)/[A-Za-z]|[A-Za-z]:\\Users\\)}],
  ["email",     qr{[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}}],
  ["em-dash",   qr{\x{2014}}],
  ["html-italic", qr{<(?:em|i)>|font-style:\s*italic}i],
);
my @priv;
if (-f $ENV{SCRUB_LOCAL}) {
  open my $fh, "<:encoding(UTF-8)", $ENV{SCRUB_LOCAL} or die;
  while (<$fh>) { chomp; next if /^\s*(#|$)/; my $skip = s/^except=(\S+)\s+// ? $1 : undef; push @priv, ["private", qr{$_}i, $skip]; }
}
my $contact = join(q{}, q{opensource-innovation}, chr(64), q{dy}, q{er-capital.com});
my $hits = 0;
for my $f (@ARGV) {
  open my $fh, "<:encoding(UTF-8)", $f or next;
  my $rel = $f =~ s{^\Q$ENV{SCRUB_ROOT}\E/?}{}r; my $md = $f =~ /\.md$/; my $fence = 0;
  while (my $line = <$fh>) {
    my $orig = $line;
    $line =~ s/\Q$contact\E//g;   # the published project contact address
    if ($md && $line =~ /^\s*(```|~~~)/) { $fence = !$fence; }
    for my $p (@pub, @priv) {
      next if defined $p->[2] && index($rel, $p->[2]) == 0;
      if ($line =~ $p->[1]) { print "$p->[0]: $rel:$.: $orig"; $hits++; }
    }
    if ($md && !$fence) {
      (my $t = $line) =~ s/`[^`]*`//g;          # ignore inline code
      $t =~ s/\*\*[^*]+\*\*//g; $t =~ s/__[^_]+__//g;   # bold is fine
      if ($t =~ /(?:^|[\s(])\*[^*\s][^*]*?[^*\s]?\*(?=[\s.,;:!?)]|$)/ && $t !~ /^\s*\*\s/ ||
          $t =~ /(?:^|[\s(])_[^_\s][^_]*?_(?=[\s.,;:!?)]|$)/) {
        print "md-italic: $rel:$.: $line"; $hits++;
      }
    }
  }
}
print $hits ? "scrub-gate: $hits hit(s)\n" : "scrub-gate: clean (".scalar(@ARGV)." files, ".scalar(@priv)." private patterns)\n";
exit($hits ? 1 : 0);
' "${files[@]}"

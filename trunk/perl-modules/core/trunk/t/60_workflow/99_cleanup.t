use strict;
use warnings;

use Test::More;
plan tests => 1;

ok(system("rm -r t/60_workflow/test_instance") == 0, 'Deleted test_instance');

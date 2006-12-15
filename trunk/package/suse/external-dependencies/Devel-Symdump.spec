#
#   - Devel-Symdump -
#   This spec file was automatically generated by cpan2rpm [ver: 1.146]
#   The following arguments were used:
#       --spec-only --version=2.0604 '--author=Andreas J. Koenig' Devel-Symdump-2.0604.tar.gz
#   For more information on cpan2rpm please visit: http://perl.arix.com/
#

%define pkgname Devel-Symdump
%define filelist %{pkgname}-%{version}-filelist
%define NVR %{pkgname}-%{version}-%{release}
%define maketest 1

name:      perl-Devel-Symdump
summary:   Devel-Symdump - dump symbol names or the symbol table
version:   2.0604
release:   1
vendor:    Andreas J. Koenig
packager:  Arix International <cpan2rpm@arix.com>
license:   Artistic
group:     Applications/CPAN
url:       http://www.cpan.org
buildroot: %{_tmppath}/%{name}-%{version}-%(id -u -n)
buildarch: noarch
prefix:    %(echo %{_prefix})
source:    Devel-Symdump-2.0604.tar.gz

%description
This little package serves to access the symbol table of perl.

=over 4

=item "Devel::Symdump->rnew(@packages)"

returns a symbol table object for all subtrees below @packages.
Nested Modules are analyzed recursively. If no package is given as
argument, it defaults to "main". That means to get the whole symbol
table, just do a "rnew" without arguments.

The global variable $Devel::Symdump::MAX_RECURSION limits the
recursion to prevent contention. The default value is set to 97, just
low enough to survive the test suite without a warning about deep
recursion.

=item "Devel::Symdump->new(@packages)"

does not go into recursion and only analyzes the packages that are
given as arguments.

=item packages, scalars, arrays, hashes, functions, ios

The methods packages(), scalars(), arrays(), hashes(), functions(),
ios(), and (for older perls) unknowns() each return an array of fully
qualified symbols of the specified type in all packages that are held
within a Devel::Symdump object, but without the leading "$", "@" or
"%". In a scalar context, they will return the number of such
symbols. Unknown symbols are usually either formats or variables that
haven't yet got a defined value.

=item as_string

=item as_HTML

As_string() and as_HTML() return a simple string/HTML representations
of the object.

=item diff

Diff() prints the difference between two Devel::Symdump objects in
human readable form. The format is similar to the one used by the
as_string method.

=item isa_tree

=item inh_tree

Isa_tree() and inh_tree() both return a simple string representation
of the current inheritance tree. The difference between the two
methods is the direction from which the tree is viewed: top-down or
bottom-up. As I'm sure, many users will have different expectation
about what is top and what is bottom, I'll provide an example what
happens when the Socket module is loaded:

=item % print Devel::Symdump->inh_tree

    AutoLoader
            DynaLoader
                    Socket
    DynaLoader
            Socket
    Exporter
            Carp
            Config
            Socket

The inh_tree method shows on the left hand side a package name and
indented to the right the packages that use the former.

=item % print Devel::Symdump->isa_tree

    Carp
            Exporter
    Config
            Exporter
    DynaLoader
            AutoLoader
    Socket
            Exporter
            DynaLoader
                    AutoLoader

The isa_tree method displays from left to right ISA relationships, so
Socket IS A DynaLoader and DynaLoader IS A AutoLoader. (Actually, they
were at the time this manpage was written)

=back

You may call both methods, isa_tree() and inh_tree(), with an
object. If you do that, the object will store the output and retrieve
it when you call the same method again later. The typical usage would
be to use them as class methods directly though.

#
# This package was generated automatically with the cpan2rpm
# utility.  To get this software or for more information
# please visit: http://perl.arix.com/
#

%prep
%setup -q -n %{pkgname}-%{version} 
chmod -R u+w %{_builddir}/%{pkgname}-%{version}

%build
grep -rsl '^#!.*perl' . |
grep -v '.bak$' |xargs --no-run-if-empty \
%__perl -MExtUtils::MakeMaker -e 'MY->fixin(@ARGV)'
CFLAGS="$RPM_OPT_FLAGS"
%{__perl} Makefile.PL `%{__perl} -MExtUtils::MakeMaker -e ' print qq|PREFIX=%{buildroot}%{_prefix}| if \$ExtUtils::MakeMaker::VERSION =~ /5\.9[1-6]|6\.0[0-5]/ '`
%{__make} 
%if %maketest
%{__make} test
%endif

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%{makeinstall} `%{__perl} -MExtUtils::MakeMaker -e ' print \$ExtUtils::MakeMaker::VERSION <= 6.05 ? qq|PREFIX=%{buildroot}%{_prefix}| : qq|DESTDIR=%{buildroot}| '`

cmd=/usr/share/spec-helper/compress_files
[ -x $cmd ] || cmd=/usr/lib/rpm/brp-compress
[ -x $cmd ] && $cmd

# SuSE Linux
if [ -e /etc/SuSE-release -o -e /etc/UnitedLinux-release ]
then
    %{__mkdir_p} %{buildroot}/var/adm/perl-modules
    %{__cat} `find %{buildroot} -name "perllocal.pod"`  \
        | %{__sed} -e s+%{buildroot}++g                 \
        > %{buildroot}/var/adm/perl-modules/%{name}
fi

# remove special files
find %{buildroot} -name "perllocal.pod" \
    -o -name ".packlist"                \
    -o -name "*.bs"                     \
    |xargs -i rm -f {}

# no empty directories
find %{buildroot}%{_prefix}             \
    -type d -depth                      \
    -exec rmdir {} \; 2>/dev/null

%{__perl} -MFile::Find -le '
    find({ wanted => \&wanted, no_chdir => 1}, "%{buildroot}");
    print "%doc  README";
    for my $x (sort @dirs, @files) {
        push @ret, $x unless indirs($x);
        }
    print join "\n", sort @ret;

    sub wanted {
        return if /auto$/;

        local $_ = $File::Find::name;
        my $f = $_; s|^\Q%{buildroot}\E||;
        return unless length;
        return $files[@files] = $_ if -f $f;

        $d = $_;
        /\Q$d\E/ && return for reverse sort @INC;
        $d =~ /\Q$_\E/ && return
            for qw|/etc %_prefix/man %_prefix/bin %_prefix/share|;

        $dirs[@dirs] = $_;
        }

    sub indirs {
        my $x = shift;
        $x =~ /^\Q$_\E\// && $x ne $_ && return 1 for @dirs;
        }
    ' > %filelist

[ -z %filelist ] && {
    echo "ERROR: empty %files listing"
    exit -1
    }

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files -f %filelist
%defattr(-,root,root)

%changelog
* Thu Nov 23 2006 root@dca02
- Initial build.
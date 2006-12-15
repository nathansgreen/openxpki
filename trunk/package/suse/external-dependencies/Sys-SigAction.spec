#
#   - Sys::SigAction -
#   This spec file was automatically generated by cpan2rpm [ver: 2.027]
#   The following arguments were used:
#       --spec-only --version=0.10 '--author=Lincoln A Baxter' Sys-SigAction-0.10.tar.gz
#   For more information on cpan2rpm please visit: http://perl.arix.com/
#

%define pkgname Sys-SigAction
%define filelist %{pkgname}-%{version}-filelist
%define NVR %{pkgname}-%{version}-%{release}
%define maketest 1

name:      perl-Sys-SigAction
summary:   Sys-SigAction - Perl extension for Consistent Signal Handling
version:   0.10
release:   1
vendor:    Lincoln A Baxter
packager:  Arix International <cpan2rpm@arix.com>
license:   Artistic
group:     Applications/CPAN
url:       http://www.cpan.org
buildroot: %{_tmppath}/%{name}-%{version}-%(id -u -n)
buildarch: noarch
prefix:    %(echo %{_prefix})
source:    Sys-SigAction-0.10.tar.gz

%description
Prior to version 5.8.0 perl implemented 'unsafe' signal handling.
The reason it is consider unsafe, is that there is a risk that a
signal will arrive, and be handled while perl is changing internal
data structures.  This can result in all kinds of subtle and not so
subtle problems.  For this reason it has always been recommended that
one do as little as possible in a signal handler, and only variables
that already exist be manipulated.

Perl 5.8.0 and later versions implements 'safe' signal handling
on platforms which support the POSIX sigaction() function.  This is
accomplished by having perl note that a signal has arrived, but deferring
the execution of the signal handler until such time as it is safe to do
so.  Unfortunately these changes can break some existing scripts, if they
depended on a system routine being interupted by the signal's arrival.
The perl 5.8.0 implementation was modified further in version 5.8.2.

From the perl 5.8.2 perlvar man page:

   The default delivery policy of signals changed in Perl 5.8.0 
   from immediate (also known as "unsafe") to deferred, also 
   known as "safe signals".  


The implementation of this changed the "sa_flags" with which
the signal handler is installed by perl, and it causes some
system routines (like connect()) to return EINTR, instead of another error
when the signal arrives.  The problem comes when the code that made 
the system call sees the EINTR code and decides it's going to call it 
again before returning. Perl doesn't do this but some libraries do, including for
instance, the Oracle OCI library.

Thus the 'deferred signal' approach (as implemented by default in
perl 5.8 and later) results in some system calls being
retried prior to the signal handler being called by perl. 
This breaks timeout logic for DBD-Oracle which works with
earlier versions of perl.  This can be particularly vexing,
the host on which a database resides is not available:  "DBI->connect()"
hangs for minutes before returning an error (and cannot even be interupted
with control-C, even when the intended timeout is only seconds). 
This is because SIGINT appears to be deferred as well.  The
result is that it is impossible to implement open timeouts with code
that looks like this in perl 5.8.0 and later:

   eval {
      local $SIG{ALRM} = sub { die "timeout" };
      alarm 2;
      $sth = DBI->connect(...);
      alarm 0;
   };
   alarm 0;
   die if $@;

The solution, if your system has the POSIX sigaction() function,
is to use perl's "POSIX::sigaction()" to install the signal handler.
With "sigaction()", one gets control over both the signal mask, and the
"sa_flags" that are used to install the handler.  Further, with perl
5.8.2 and later, a 'safe' switch is provided which can be used to ask
for safe(r) signal handling. 
   
Using sigaction() ensures that the system call won't be
resumed after it's interrupted, so long as die is called
within the signal handler.  This is no longer the case when 
one uses $SIG{name} to set signal
handlers in perls >= 5.8.0.

The usage of sigaction() is not well documented however, and in perl
versions less than 5.8.0, it does not work at all. (But that's OK, because
just setting $SIG does work in that case.)  Using sigaction() requires
approximately 4 or 5 lines of code where previously one only had to set
a code reference into the %SIG hash.

Unfortunately, at least with perl 5.8.0, the result is that doing this
effectively reverts to the 'unsafe' signals behavior.  It is not clear
whether this would be the case in perl 5.8.2, since the safe flag can be used
to ask for safe signal handling.  I suspect this separates the logic
which uses the "sa_flags" to install the handler, and whether deferred
signal handling is used.

The reader should also note, that the behavior of the 'safe' 
attribute is not consistent with what this author expected. 
Specifically, it appears to disable signal masking. This can be
examined further in the t/safe.t and the t/mask.t regression tests.
Never-the-less, Sys::SigAction provides an easy mechanism for
the user to recover the pre-5.8.0 behavior for signal handling, and the
mask attribute clearly works. (see t/mask.t) If one is looking for
specific safe signal handling behavior that is considered broken,
and the breakage can be demonstrated, then a patch to t/safe.t would be 
most welcome.

This module wraps up the POSIX:: routines and objects necessary to call
sigaction() in a way that is as efficient from a coding perspective as just
setting a localized $SIG{SIGNAL} with a code reference.  Further, the
user has control over the "sa_flags" passed to sigaction().  By default,
if no additional args are passed to sigaction(), then the signal handler
will be called when a signal (such as SIGALRM) is delivered.

Since sigaction() is not fully functional in perl versions less than
5.8, this module implements equivalent behavior using the standard
%SIG array.  The version checking and implementation of the 'right'
code is handled by this module, so the user does not have to write perl
version dependent code.  The attrs hashref argument to set_sig_handler()
is silently ignored, in perl versions less than 5.8.  This module has
been tested with perls as old as 5.005 on solaris.

It is hoped that with the use of this module, your signal handling
behavior can be coded in a way that does not change from one perl version
to the next, and that sigaction() will be easier for you to use.

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
    print "%doc  Changes README";
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
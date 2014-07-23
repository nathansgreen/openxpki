# OpenXPKI::Server::Workflow::Activity::Tools::RenderSubject
# Written by Oliver Welterfor the OpenXPKI Project 2013
# Copyright (c) 2013 by The OpenXPKI Project

package OpenXPKI::Server::Workflow::Activity::Tools::RenderSubject;

use strict;

use OpenXPKI::Debug;
use OpenXPKI::Exception;
use OpenXPKI::Serialization::Simple;
use OpenXPKI::Server::Context qw( CTX );
use English;
use Template;
use Data::Dumper;

use base qw( OpenXPKI::Server::Workflow::Activity );

sub execute {
    my $self     = shift;
    my $workflow = shift;

    ##! 8: 'Start'

    my $context = $workflow->context();
    my $config = CTX('config');

    my $tt = new Template();
    my $ser = new OpenXPKI::Serialization::Simple;
    my $result;


    # Get the profile name and style
    my $profile = $context->param('cert_profile');
    my $style = $context->param('cert_subject_style');

    if (!$profile  || !$style) {
        OpenXPKI::Exception->throw(
            message => 'I18N_OPENXPKI_SERVER_WORKFLOW_ACTIVITY_TOOLS_RENDER_SUBJECT_NO_PROFILE',
            params  => {
                PROFILE => $profile,
                STYLE   => $style,
            }
        );
    }

    # Render the DN - get the input data from the context
    my $template_vars = $ser->deserialize(  $context->param('cert_subject_parts') );
    my $subject_vars = {};
    # Remove the "cert_subject" prefix (old ui only)
    ##! 16: 'Deserialized cert_subject_parts ' . Dumper $template_vars
    foreach my $key (keys %{$template_vars}) {
        my $template_key;
        if ($key =~ m{ \A cert_subject_(.*) \z }xms) {
            $template_key = $1;
        } else {
            $template_key = $key;
        }
        $subject_vars->{$template_key} = $template_vars->{$key};
        # Escape Comma
        $subject_vars->{$template_key} =~ s{,}{\\,}xmsg;
    }

    ##! 16: 'Cleaned subject_vars' . Dumper $subject_vars

    CTX('log')->log(
        MESSAGE => "Subject render input vars " . Dumper $subject_vars,
        PRIORITY => 'debug',
        FACILITY => [ 'application', ],
    );

    my $cert_subject = CTX('api')->render_subject_from_template({
        PROFILE => $profile,
        STYLE   => $style,
        VARS    => $subject_vars
    });

    if (!$cert_subject) {
        OpenXPKI::Exception->throw(
            message => 'I18N_OPENXPKI_SERVER_WORKFLOW_ACTIVITY_TOOLS_RENDER_SUBJECT_DN_RESULT_EMPTY',
            params  => {
                PROFILE => $profile,
                STYLE   => $style,
            }
        );
    }

    CTX('log')->log(
        MESSAGE => "Rendering subject: $cert_subject",
        PRIORITY => 'info',
        FACILITY => [ 'application', ],
    );



    # This is a temporary hack to handle old ui workflows -
    # we "blindly copy" the pkcs10 sans if the new cert_san_parts is not set
    # The pkcs10 alternative path should be removed after UI change
    my $cert_san_parts  = $context->param('cert_san_parts');
    my $pkcs10 = $context->param('pkcs10');

    my $extra_san = {};
    if ($cert_san_parts) {
        $extra_san = $ser->deserialize( $cert_san_parts );
    } elsif ($pkcs10) {
        my $obj = OpenXPKI::Crypto::CSR->new( DATA => $pkcs10, TOKEN => CTX('api')->get_default_token() );
        $extra_san = $obj->get_subject_alt_names({ FORMAT => 'HASH' });
    }

    ##! 32: 'extra san' . Dumper $extra_san

    my $san_list;
    # Try to render using the template mode, will return undef if there is no
    # rendering rule

    $san_list = CTX('api')->render_san_from_template({
        PROFILE => $profile,
        STYLE   => $style,
        VARS    => $subject_vars,
        ADDITIONAL => $extra_san || {},
    });

    # No SAN template exists - if we have extra san just map them to the
    # array ref structure required by the csr persister
    if (!$san_list && $extra_san) {
        my $san_names = CTX('api')->list_supported_san();

        # create a nested has to remove duplicates
        my $san_items = {};
        foreach my $type (keys %{$extra_san}) {
            foreach my $value (@{$extra_san->{$type}}) {
                $san_items->{$type}->{$value} = 1 if($value);
            }
        }

        # Map the items hash to san_array structure used by our crypto engine
        foreach my $type (keys %{$san_items}) {
            foreach my $value (keys %{$san_items->{$type}}) {
                push @{$san_list}, [ $type, $value ] if ($value);
            }
        }

        CTX('log')->log(
            MESSAGE => "San template empty but extra_san present",
            PRIORITY => 'debug',
            FACILITY => [ 'application', ],
        );
    }

    ##! 64: "Entries in san_list \n" .  Dumper $san_list;

    # store in context
    $context->param('cert_subject' => $cert_subject);

    # Current serialize creates an "UNDEF" string which fails an easy "is empty" test
    if ($san_list) {
        $context->param('cert_subject_alt_name' => $ser->serialize( $san_list ));
    } else {
        $context->param('cert_subject_alt_name' => '');
    }

    # If the SAN come from the internal rendering we need to set the source
    # parameter for as this is required by persist_csr

    my $source_ref = $ser->deserialize($context->param('sources'));
    if (!$source_ref->{cert_subject_alt_name_parts} && !$source_ref->{cert_subject_alt_name}) {
        $source_ref->{cert_subject_alt_name} = 'PROFILE';
    }
    $context->param('sources' => $ser->serialize( $source_ref ));


    return 1;

}

1;
__END__

=head1 Name

OpenXPKI::Server::Workflow::Activity::Tools::RenderSubject;

=head1 Description

Take the input parameters provided by the ui and render the subject and
subject alternative according to the profiles template definition.
The SAN part is made up from two seperate sources:

=head2 templated SAN entries

Define template fields in the ui.subject section of you profile and use them in the
rendering information in subject.san the same way you do for the subject.

Example:

  ui:
    subject:
    - hostname
    - hostname2
    - port

  subject:
    dn: CN=[% hostname %][% IF port AND port != 443 %]:[% port %][% END %],DC=Test Deployment,DC=OpenXPKI,DC=org
    san:
      dns:
      - "[% hostname %]"
      - "[% FOREACH entry = hostname2 %][% entry %]|[% END %]"

This will end up with a certificate which has the hostname as CN and
additionally copied to the SAN. A second hostname is also put into the SAN
section, empty or duplicate values are purged, in case that hostname2
is an array (multi input field), you need to use a foreach loop and end
each entry with the pipe symbol |. Hint: The foreach loop automagically
degrades if the given value is a scalar or even undef, so use foreach
whenever a list is possible.

Templated entries are displayed to the user during request but can not be
removed by the user.

=head2 free SAN entries

To enable free SAN entries add a section ui.san next to you ui.subject. The
form fields MUST have a key that fits any of the allowed SAN items (e.g DNS,
IP, OID) and the value must be given in the approriate format for this item.
The users input is mapped without further templating to the san section of the
certificate (duplicate items and and leading/trailing whitespace are removed).

Note: If you upload a PKCS10 request having SANs, those ones that match the
available type are prefilled. Items that do not match a defined type are
discarded.

Example:

   # In the style definition
   ui:
     san:
        - san_dns
        - san_ip

   # In the template section
   template:
     san_dns:
       id: dns
       label: I18N_OPENXPKI_SAN_DNS
       description: I18N_OPENXPKI_SAN_DNS_DESCRIPTION
       type: freetext
       width: 40
       min: 0
       max: 20

    san_ip:
       id: ip
       label: I18N_OPENXPKI_SAN_IP
       description: I18N_OPENXPKI_SAN_IP_DESCRIPTION
       type: freetext
       width: 15
       min: 0
       max: 20

The above code will present the user up to 20 fields each to enter IPs or DNS
names. Each entry will show up "as is" as a single san entry.

=head2 context values

=over

=item cert_subject_parts

The main subject parameters, used for rendering the subject dn and in template
mode for the san. The "cert_subject_" prefix is removed from the keys name.

=item cert_profile

Determines the used profile.

=item cert_subject_style

Determines the used profile substyle-

=item cert_subject

Holds the result for the subject.

=item cert_subject_alt_name

Holds the result for the san section.

=back


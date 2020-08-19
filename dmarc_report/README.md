dmarc_report.py V1.0.0
======================

Parses DMARC xml reports and writes results to syslog.

Requires syslog-ng configuration /etc/syslog-ng/conf.d/dmarc_report.conf:

filter f_dmarc_report { program('^dmarc_report') };

destination d_dmarc_report {
    file(
        "/var/log/cs-gateway/dmarc_report.$YEAR-$MONTH-$DAY.log"
        create_dirs(yes)
        template("$DATE $MSGHDR$MESSAGE\n")
    );
};
 
log { source(s_sys); filter(f_dmarc_report); destination(d_dmarc_report); };
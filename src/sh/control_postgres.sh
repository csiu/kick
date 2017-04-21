SCRIPT=$0
DATADIR=~/repo/kick/data/database/postgres
USAGE="""Usage: sh ${SCRIPT}
Function:
Options:
-h          print help message
-s          start database
-e          end/stop database
"""

## print usage if no args
if [ $# == 0 ]; then echo "${USAGE}" && exit 1 ; fi

## user can pass args in any order using flags
while getopts hse option
do
  case "${option}" in
    h) echo "$USAGE" && exit;;
    s) ACTION=start;;
    e) ACTION=stop;;
  esac
done

## do something...
echo "pg_ctl -D ${DATADIR} ${ACTION}"
pg_ctl -D ${DATADIR} ${ACTION}

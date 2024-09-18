cleanup_autotools(){
	export LD_LIBRARY_PATH=$(echo ${LD_LIBRARY_PATH} | awk -v RS=: -v ORS=: '/autotools/ {next} {print}' | sed 's/:*$//')
	export PATH=$(echo ${PATH} | awk -v RS=: -v ORS=: '/autotools/ {next} {print}' | sed 's/:*$//')
	unset AUTOTOOLS_ROOT
	unset AUTOTOOLS_VERSION
	unset AUTOTOOLS_COMMIT
	unset AUTOTOOLS_REVISION
}

cleanup_fedra(){
	export LD_LIBRARY_PATH=$(echo ${LD_LIBRARY_PATH} | awk -v RS=: -v ORS=: '/FEDRA/ {next} {print}' | sed 's/:*$//')
	export PATH=$(echo ${PATH} | awk -v RS=: -v ORS=: '/FEDRA/ {next} {print}' | sed 's/:*$//')
	unset FEDRA_ROOT
	unset FEDRA_VERSION
	unset FEDRA_COMMIT
	unset FEDRA_REVISION
	unset FEDRA_HASH
}

cleanup_sndsw(){
	export LD_LIBRARY_PATH=$(echo ${LD_LIBRARY_PATH} | awk -v RS=: -v ORS=: '/sndsw/ {next} {print}' | sed 's/:*$//')
	export PATH=$(echo ${PATH} | awk -v RS=: -v ORS=: '/sndsw/ {next} {print}' | sed 's/:*$//')
	unset SNDSW_ROOT
	unset SNDSW_VERSION
	unset SNDSW_COMMIT
	unset SNDSW_REVISION
	unset SNDSW_HASH
}

cleanup_autotools
cleanup_fedra
cleanup_sndsw



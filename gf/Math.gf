abstract Math = Grammar ** {
    cat
        Formula;
    fun
        formulaToken : Formula;

        formulaAsSgNP : Formula -> NP;
        formulaAsPlNP : Formula -> NP;


        integrable : A;
        wrt_Prep : Prep;
        derivation : N;
        integral : N;
}

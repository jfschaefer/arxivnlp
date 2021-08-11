concrete MathEng of Math = GrammarEng ** open ResEng, ParadigmsEng in {
    lincat
        Formula = Str;
    lin
        formulaToken = "FORMULA";

        formulaAsSgNP f = lin NP { s = table { _ => f } ; a = AgP3Sg Neutr } ;
        formulaAsPlNP f = lin NP { s = table { _ => f } ; a = AgP3Pl Neutr } ;
        
        integrable = mkA "integrable";
        wrt_Prep = mkPrep "with respect to";
        derivation = mkN "derivation";
        integral = mkN "integral";
}

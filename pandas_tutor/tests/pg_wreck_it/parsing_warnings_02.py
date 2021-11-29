# https://www.shanelynn.ie/pandas-iloc-loc-select-rows-and-columns-dataframe/
import pandas as pd
import io
csv = """
first_name,last_name,company_name,address,city,county,postal,phone1,phone2,email,web
Aleshia,Tomkiewicz,Alan D Rosenburg Cpa Pc,14 Taylor St,St. Stephens Ward,Kent,CT2 7PP,01835-703597,01944-369967,atomkiewicz@hotmail.com,http://www.alandrosenburgcpapc.co.uk
Evan,Zigomalas,Cap Gemini America,5 Binney St,Abbey Ward,Buckinghamshire,HP11 2AX,01937-864715,01714-737668,evan.zigomalas@gmail.com,http://www.capgeminiamerica.co.uk
France,Andrade,"Elliott, John W Esq",8 Moor Place,East Southbourne and Tuckton W,Bournemouth,BH6 3BE,01347-368222,01935-821636,france.andrade@hotmail.com,http://www.elliottjohnwesq.co.uk
Ulysses,Mcwalters,"Mcmahan, Ben L",505 Exeter Rd,Hawerby cum Beesby,Lincolnshire,DN36 5RP,01912-771311,01302-601380,ulysses@hotmail.com,http://www.mcmahanbenl.co.uk
Tyisha,Veness,Champagne Room,5396 Forth Street,Greets Green and Lyng Ward,West Midlands,B70 9DT,01547-429341,01290-367248,tyisha.veness@hotmail.com,http://www.champagneroom.co.uk
Eric,Rampy,"Thompson, Michael C Esq",9472 Lind St,Desborough,Northamptonshire,NN14 2GH,01969-886290,01545-817375,erampy@rampy.co.uk,http://www.thompsonmichaelcesq.co.uk
Marg,Grasmick,Wrangle Hill Auto Auct & Slvg,7457 Cowl St #70,Bargate Ward,Southampton,SO14 3TY,01865-582516,01362-620532,marg@hotmail.com,http://www.wranglehillautoauctslvg.co.uk
Laquita,Hisaw,In Communications Inc,20 Gloucester Pl #96,Chirton Ward,Tyne & Wear,NE29 7AD,01746-394243,01590-982428,laquita@yahoo.com,http://www.incommunicationsinc.co.uk
Lura,Manzella,Bizerba Usa Inc,929 Augustine St,Staple Hill Ward,South Gloucestershire,BS16 4LL,01907-538509,01340-713951,lura@hotmail.com,http://www.bizerbausainc.co.uk
Yuette,Klapec,Max Video,45 Bradfield St #166,Parwich,Derbyshire,DE6 1QN,01903-649460,01933-512513,yuette.klapec@klapec.co.uk,http://www.maxvideo.co.uk
Fernanda,Writer,K & R Associates Inc,620 Northampton St,Wilmington,Kent,DA2 7PP,01630-202053,01687-879391,fernanda@writer.co.uk,http://www.krassociatesinc.co.uk
Charlesetta,Erm,"Cain, John M Esq",5 Hygeia St,Loundsley Green Ward,Derbyshire,S40 4LY,01276-816806,01517-624517,charlesetta_erm@gmail.com,http://www.cainjohnmesq.co.uk
Corrinne,Jaret,Sound Vision Corp,2150 Morley St,Dee Ward,Dumfries and Galloway,DG8 7DE,01625-932209,01642-322954,corrinne_jaret@gmail.com,http://www.soundvisioncorp.co.uk
Niesha,Bruch,Rowley/hansell Petetin,24 Bolton St,"Broxburn, Uphall and Winchburg",West Lothian,EH52 5TL,01874-856950,01342-793603,niesha.bruch@yahoo.com,http://www.rowleyhansellpetetin.co.uk
Rueben,Gastellum,Industrial Engineering Assocs,4 Forrest St,Weston-Super-Mare,North Somerset,BS23 3HG,01976-755279,01956-535511,rueben_gastellum@gastellum.co.uk,http://www.industrialengineeringassocs.co.uk
Michell,Throssell,Weiss Spirt & Guyer,89 Noon St,Carbrooke,Norfolk,IP25 6JQ,01967-580851,01672-496478,mthrossell@throssell.co.uk,http://www.weissspirtguyer.co.uk
Edgar,Kanne,"Crowan, Kenneth W Esq",99 Guthrie St,New Milton,Hampshire,BH25 5DF,01326-532337,01666-638176,edgar.kanne@yahoo.com,http://www.crowankennethwesq.co.uk
Dewitt,Julio,Rittenhouse Motor Co,7 Richmond St,Parkham,Devon,EX39 5DJ,01253-528327,01241-964675,dewitt.julio@hotmail.com,http://www.rittenhousemotorco.co.uk
"""
df = pd.read_csv(io.StringIO(csv))
df.set_index("last_name", inplace=True)

df[df["first_name" == "Dewitt"]]

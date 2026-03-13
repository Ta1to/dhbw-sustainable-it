First run:
`sc.exe create Scaphandre binPath="C:\Program Files (x86)\scaphandre\scaphandre.exe prometheus-push -H localhost -s 5 -p 9091" DisplayName="Scaphandre" start=auto`

Then:
`sc.exe start Scaphandre`
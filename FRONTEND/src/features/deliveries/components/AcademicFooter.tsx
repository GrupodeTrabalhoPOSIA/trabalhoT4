import { academicProject } from '../utils/academicProject';

export default function AcademicFooter() {
  return <footer className="delivery-academic-footer">
    <div><strong>{academicProject.institution}</strong><p>{academicProject.course}<br />{academicProject.subject}<br />Prof. {academicProject.professor}</p></div>
    <div><strong>Grupo de trabalho</strong><ul>{academicProject.participants.map(name => <li key={name}>{name}</li>)}</ul></div>
  </footer>;
}
